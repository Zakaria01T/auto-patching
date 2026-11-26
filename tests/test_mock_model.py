import json
from pathlib import Path
import urllib.error
import urllib.request

import pytest

from patcher import generate
from patcher.mock_model import MALFORMED, MockModel, gold_replies, serve, target
from patcher.prompts import ROOT

GOLD = {json.loads(line)["source"]: json.loads(line)
        for line in (ROOT / "training/gold.jsonl").read_text().splitlines()}


def call(base_url, gold="gold:corpus/train/gold_sqli_01", tmp_path=None, **kwargs):
    row = GOLD[gold]
    finding = dict(row["finding"], file="source.py" if row["finding"]["language"] == "python" else "source.c")
    case = ROOT / gold.split(":", 1)[1]
    extra = dict(db_driver="sqlite3", driver_evidence="caller: SQLite connection") if row["cwe"] == "CWE-89" else {}
    return generate(finding, row["vulnerable_code"], (case / "test.txt").read_text(),
                    base_url=base_url, timeout=10, **extra, **kwargs)


@pytest.mark.parametrize("gold", sorted(GOLD))
def test_good_returns_gold_repair_in_production_layout(gold):
    row = GOLD[gold]
    with serve("good") as (base_url, model):
        raw = call(base_url, gold)
    language = row["finding"]["language"]
    assert raw.startswith(f"```{language}\n")
    code, rest = raw[len(language) + 4:].split("\n```\n", 1)
    assert "#include" not in code
    assert code.strip() in row["repair"]
    assert rest.startswith("EXPLANATION: " + row["explanation"])
    if language == "c":
        assert rest.splitlines()[-1].startswith("INCLUDES: <stdio.h>")
    assert len(model.calls) == 1


def test_unchanged_returns_vulnerable_function():
    row = GOLD["gold:corpus/train/gold_sqli_01"]
    with serve("unchanged") as (base_url, _):
        raw = call(base_url)
    assert raw == f"```python\n{row['vulnerable_code'].strip()}\n```\nEXPLANATION: The function is already safe."


def test_malformed_and_empty():
    with serve("malformed") as (base_url, _):
        assert call(base_url) == MALFORMED
    assert "```" not in MALFORMED and "EXPLANATION:" not in MALFORMED
    with serve("empty") as (base_url, _):
        assert call(base_url) == ""


def test_modes_used_one_per_call_last_repeats():
    with serve(["malformed", "empty", "good"]) as (base_url, model):
        answers = [call(base_url) for _ in range(4)]
    assert answers[0] == MALFORMED and answers[1] == ""
    assert answers[2] == answers[3] and answers[2].startswith("```python\ndef find_invoice")
    assert len(model.calls) == 4


def test_generate_sees_configured_tag_and_logs(tmp_path):
    config = tmp_path / "model.yaml"
    config.write_text('model:\n  tag: "qwen2.5-coder:7b"\n  temperature: 0.0\n')
    log = tmp_path / "calls.jsonl"
    with serve("good") as (base_url, model):
        call(base_url, config_path=config, log_path=log)
    assert model.calls[0]["model"] == "qwen2.5-coder:7b"
    assert model.calls[0]["options"]["temperature"] == 0.0
    record = json.loads(log.read_text())
    assert record["status"] == "received_unvalidated" and record["model_tag"] == "qwen2.5-coder:7b"


def test_good_without_reply_fails_loudly():
    with serve("good", replies={}) as (base_url, _):
        with pytest.raises(urllib.error.HTTPError) as error:
            call(base_url)
    assert "find_invoice" in json.loads(error.value.read())["error"]


def test_replies_file_overrides_gold():
    reply = "```python\ndef find_invoice(conn, number):\n    return None\n```\nEXPLANATION: Custom."
    with serve("good", replies={"find_invoice": reply}) as (base_url, _):
        assert call(base_url) == reply


def test_rejects_stream_and_unknown_paths():
    with serve() as (base_url, model):
        body = json.dumps({"model": "m", "messages": [], "stream": True}).encode()
        with pytest.raises(urllib.error.HTTPError) as error:
            urllib.request.urlopen(urllib.request.Request(base_url + "/api/chat", body), timeout=5)
        assert error.value.code == 400
        with pytest.raises(urllib.error.HTTPError) as error:
            urllib.request.urlopen(base_url + "/v1/models", timeout=5)  # only chat is served
        assert error.value.code == 404
        assert json.load(urllib.request.urlopen(base_url + "/api/version", timeout=5)) == {"version": "mock"}
    assert model.calls == []


def test_unknown_mode_rejected():
    with pytest.raises(ValueError):
        MockModel("broken")


def test_target_names():
    assert target("Vulnerable function:\n```c\nvoid copy_name(const char *in) {\n}\n```")[2] == "copy_name"
    assert target("Vulnerable function:\n```python\nasync def page(x):\n    pass\n```")[2] == "page"
    assert len(gold_replies()) == 8


# ---------- OpenAI-compatible API (vLLM, for example the Modal server) ----------
from unittest.mock import patch
from patcher.generate import read_config

OPENAI_CONFIG = 'model:\n  tag: "Qwen/Qwen2.5-Coder-7B-Instruct"\n  temperature: 0.0\n  api: "openai"\n'


def test_config_api_default_and_modal_file(tmp_path):
    assert read_config(ROOT / "configs/model.yaml")["api"] == "ollama"
    assert read_config(ROOT / "configs/model.modal.yaml") == dict(
        tag="Qwen/Qwen2.5-Coder-7B-Instruct", temperature=0.0, api="openai")
    bad = tmp_path / "model.yaml"
    bad.write_text('model:\n  tag: "m"\n  temperature: 0.0\n  api: "grpc"\n')
    with pytest.raises(ValueError, match="optional api"):
        read_config(bad)


@pytest.mark.parametrize("mode", ["good", "malformed", "empty", "unchanged"])
def test_openai_api_through_mock(tmp_path, mode):
    config = tmp_path / "model.yaml"
    config.write_text(OPENAI_CONFIG)
    log = tmp_path / "calls.jsonl"
    with serve(mode) as (base_url, model):
        raw = call(base_url, config_path=config, log_path=log, options=dict(num_predict=2048, seed=1))
    sent = model.calls[0]
    assert sent["model"] == "Qwen/Qwen2.5-Coder-7B-Instruct" and sent["stream"] is False
    assert sent["temperature"] == 0.0 and sent["max_tokens"] == 2048 and sent["seed"] == 1
    assert "options" not in sent
    record = json.loads(log.read_text())
    assert record["api"] == "openai" and record["status"] == "received_unvalidated"
    assert record["raw_response"] == raw and record["done_reason"] == "stop"
    if mode == "good":
        assert raw.startswith("```python\ndef find_invoice")


def test_switch_with_environment_only(tmp_path, monkeypatch):
    config = tmp_path / "model.yaml"
    config.write_text(OPENAI_CONFIG)
    with serve("good") as (base_url, model):
        monkeypatch.setenv("MODEL_CONFIG", str(config))
        monkeypatch.setenv("MODEL_BASE_URL", base_url + "/")
        row = GOLD["gold:corpus/train/gold_sqli_01"]
        raw = generate(row["finding"], row["vulnerable_code"], "Normal result: one row",
                       db_driver="sqlite3", driver_evidence="caller")
    assert raw.startswith("```python") and model.calls[0]["model"] == "Qwen/Qwen2.5-Coder-7B-Instruct"


def test_openai_rejects_unknown_option(tmp_path):
    config = tmp_path / "model.yaml"
    config.write_text(OPENAI_CONFIG)
    with serve() as (base_url, model):
        with pytest.raises(ValueError, match="num_ctx"):
            call(base_url, config_path=config, options=dict(num_ctx=4096))
    assert model.calls == []


def test_openai_cut_answer_and_api_key_not_logged(tmp_path, monkeypatch):
    config = tmp_path / "model.yaml"
    config.write_text(OPENAI_CONFIG)
    log = tmp_path / "calls.jsonl"
    monkeypatch.setenv("MODEL_API_KEY", "secret-test-key")
    reply = dict(model="Qwen/Qwen2.5-Coder-7B-Instruct", usage=dict(prompt_tokens=5, completion_tokens=7),
                 choices=[dict(finish_reason="length", message=dict(content="```python\ndef f("))])
    import io
    with patch("urllib.request.urlopen", return_value=io.BytesIO(json.dumps(reply).encode())) as sent:
        with pytest.raises(RuntimeError, match="incomplete"):
            call("http://model.test", config_path=config, log_path=log)
    request = sent.call_args.args[0]
    assert request.full_url == "http://model.test/v1/chat/completions"
    assert request.get_header("Authorization") == "Bearer secret-test-key"
    record = json.loads(log.read_text())
    assert record["done_reason"] == "length" and record["eval_count"] == 7 and record["status"] == "error"
    assert "secret-test-key" not in log.read_text() and "model.test" not in log.read_text()
