"""Thin model transport (Ollama or OpenAI-compatible API). P2 owns response validation, insertion, and diff generation."""
from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
import re
import time
import urllib.request

from .prompts import ROOT, PROMPT_VERSION, build_prompts, load_example, resolve_driver, select_example

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "http://localhost:11434"
# Ollama option name -> OpenAI request field. Other options are rejected for the openai api.
OPENAI_FIELDS = dict(temperature="temperature", num_predict="max_tokens", seed="seed", top_p="top_p")


def read_config(path):
    """Return dict(tag, temperature, api) from the fixed model.yaml schema, without a new dependency.

    `api` is optional: "ollama" (default, POST /api/chat) or "openai" (POST /v1/chat/completions,
    as served by vLLM, for example on Modal).
    """
    text = Path(path).read_text(encoding="utf-8")
    match = re.fullmatch(r'\s*model:\s*\n\s+tag:\s*"([^"\n]+)"\s*\n\s+temperature:\s*(0(?:\.\d+)?|1(?:\.0+)?)\s*'
                         r'(?:\n\s+api:\s*"(ollama|openai)"\s*)?', text)
    if not match:
        raise ValueError('expected model.yaml schema: model with quoted tag, temperature in [0, 1] '
                         'and optional api "ollama" or "openai"')
    return dict(tag=match[1], temperature=float(match[2]), api=match[3] or "ollama")


def _request(api, base_url, tag, system, user, generation):
    """Return (url, payload) for the configured API."""
    messages = [dict(role="system", content=system), dict(role="user", content=user)]
    if api == "ollama":
        return base_url + "/api/chat", dict(model=tag, messages=messages, stream=False, options=generation)
    unknown = sorted(set(generation) - set(OPENAI_FIELDS))
    if unknown:
        raise ValueError(f"options not supported by the openai api: {unknown}")
    payload = dict(model=tag, messages=messages, stream=False)
    payload.update({OPENAI_FIELDS[k]: v for k, v in generation.items()})
    return base_url + "/v1/chat/completions", payload


def _read(api, result):
    """Return (content, model, complete, counters) from either API's reply."""
    if api == "ollama":
        counters = {k: result.get(k) for k in ("prompt_eval_count", "eval_count", "total_duration",
                                                "load_duration", "eval_duration", "done_reason")}
        return result.get("message", {}).get("content"), result.get("model"), result.get("done") is True, counters
    choice = (result.get("choices") or [{}])[0]
    usage = result.get("usage") or {}
    counters = dict(prompt_eval_count=usage.get("prompt_tokens"), eval_count=usage.get("completion_tokens"),
                    done_reason=choice.get("finish_reason"))
    content = (choice.get("message") or {}).get("content")
    return content, result.get("model"), choice.get("finish_reason") == "stop", counters


def generate(finding, vulnerable_function, expected_behavior, db_driver=None, example=None,
             *, driver_evidence=None, sql_present=None, config_path=None,
             base_url=None, timeout=300, options=None, log_path=None):
    """Return raw response only; never execute, parse, insert, or generate a patch.

    config_path: this argument, else MODEL_CONFIG (relative to the repo root), else configs/model.yaml.
    base_url: this argument, else the MODEL_BASE_URL environment variable, else local Ollama.
    MODEL_API_KEY, when set, is sent as a bearer token; it is never logged.
    The default timeout covers a hosted server waking up (about 3 minutes on Modal).
    """
    config = read_config(config_path or ROOT / os.environ.get("MODEL_CONFIG", "configs/model.yaml"))
    tag, temperature, api = config["tag"], config["temperature"], config["api"]
    base_url = (base_url or os.environ.get("MODEL_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
    generation = dict(options or {})
    if "temperature" in generation:
        raise ValueError("temperature must come from configs/model.yaml")
    generation["temperature"] = temperature
    example = select_example(finding) if example is None else example
    db_driver, driver_evidence = resolve_driver(vulnerable_function, db_driver, driver_evidence)
    system, user = build_prompts(finding, vulnerable_function, expected_behavior, db_driver, example,
                                driver_evidence=driver_evidence, sql_present=sql_present)
    sample = load_example(example)
    record = dict(model_tag=tag, api=api, prompt_version=PROMPT_VERSION, temperature=temperature,
                  language=finding["language"], rule_id=finding["rule_id"], cwe=finding["cwe"],
                  file=finding["file"], line=finding["line"], example_id=sample["id"],
                  example_path=sample["path"], example_reviewer=sample["reviewer"],
                  timestamp=datetime.now(timezone.utc).isoformat(), generation_parameters=generation,
                  raw_response=None, status="error")
    url, payload = _request(api, base_url, tag, system, user, generation)
    headers = {"Content-Type": "application/json"}
    if os.environ.get("MODEL_API_KEY"):
        headers["Authorization"] = "Bearer " + os.environ["MODEL_API_KEY"]
    request = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers)
    start = time.monotonic()
    try:
        # urllib follows a 303 with a GET: that is how Modal hands back a reply that took over 150 s.
        with urllib.request.urlopen(request, timeout=timeout) as response:
            result = json.load(response)
        content, model, complete, counters = _read(api, result)
        record["raw_response"] = content
        record.update(counters)
        if model != tag or not complete or not isinstance(content, str):
            raise RuntimeError("incomplete response or unexpected model identity")
        record["status"] = "received_unvalidated"
        return record["raw_response"]
    except Exception as exc:
        record["error_type"] = type(exc).__name__  # avoid credentials in URL/error messages
        raise
    finally:
        record["latency_seconds"] = time.monotonic() - start
        encoded = json.dumps(record, ensure_ascii=False)
        logger.info("%s", encoded)
        if log_path is not None:
            with Path(log_path).open("a", encoding="utf-8") as stream:
                stream.write(encoded + "\n")
