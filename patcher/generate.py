"""Thin Ollama transport. P2 owns response validation, insertion, and diff generation."""
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import re
import time
import urllib.request

from .prompts import ROOT, PROMPT_VERSION, build_prompts, load_example, select_example

logger = logging.getLogger(__name__)


def read_config(path):
    # Parse only the project's current two-field YAML schema without a new dependency.
    text = Path(path).read_text(encoding="utf-8")
    match = re.fullmatch(r'\s*model:\s*\n\s+tag:\s*"([^"\n]+)"\s*\n\s+temperature:\s*(0(?:\.\d+)?|1(?:\.0+)?)\s*', text)
    if not match:
        raise ValueError("expected model.yaml schema: model with quoted tag and temperature in [0, 1]")
    return match[1], float(match[2])


def generate(finding, vulnerable_function, expected_behavior, db_driver=None, example=None,
             *, driver_evidence=None, sql_present=None, config_path=ROOT / "configs/model.yaml",
             base_url="http://localhost:11434", timeout=120, options=None, log_path=None):
    """Return raw response only; never execute, parse, insert, or generate a patch."""
    tag, temperature = read_config(config_path)
    generation = dict(options or {})
    if "temperature" in generation:
        raise ValueError("temperature must come from configs/model.yaml")
    generation["temperature"] = temperature
    example = select_example(finding) if example is None else example
    system, user = build_prompts(finding, vulnerable_function, expected_behavior, db_driver, example,
                                driver_evidence=driver_evidence, sql_present=sql_present)
    sample = load_example(example)
    record = dict(model_tag=tag, prompt_version=PROMPT_VERSION, temperature=temperature,
                  language=finding["language"], rule_id=finding["rule_id"], cwe=finding["cwe"],
                  file=finding["file"], line=finding["line"], example_id=sample["id"],
                  example_path=sample["path"], example_reviewer=sample["reviewer"],
                  timestamp=datetime.now(timezone.utc).isoformat(), generation_parameters=generation,
                  raw_response=None, status="error")
    payload = dict(model=tag, messages=[dict(role="system", content=system), dict(role="user", content=user)],
                   stream=False, options=generation)
    request = urllib.request.Request(base_url.rstrip("/") + "/api/chat",
                                     data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    start = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            result = json.load(response)
        record["raw_response"] = result.get("message", {}).get("content")
        for key in ("prompt_eval_count", "eval_count", "total_duration", "load_duration", "eval_duration", "done_reason"):
            record[key] = result.get(key)
        if result.get("model") != tag or result.get("done") is not True or not isinstance(record["raw_response"], str):
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
