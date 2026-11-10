import io
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from patcher import build_prompts, generate, select_example
from patcher.prompts import ROOT, load_example


def finding(language="python", cwe="CWE-89"):
    return dict(file="source.py" if language == "python" else "source.c", line=2,
                cwe=cwe, severity="high", rule_id="test-rule", language=language,
                owasp="A03:2021-Injection" if language == "python" else None)


def build(**changes):
    args = dict(finding=finding(), vulnerable_function="def f(conn, x):\n    return conn.execute('SELECT ' + x)",
                expected_behavior='Input: x = "1"\nNormal result: one row', db_driver="sqlite3",
                example="corpus/train/gold_sqli_01", driver_evidence="training/validate_gold.py: db() uses sqlite3.connect")
    args.update(changes)
    return build_prompts(**args)


def test_prompt_has_all_inputs_and_contract():
    system, user = build()
    for value in finding().values():
        assert str(value) in user
    assert "Normal result: one row" in user
    assert "def f(conn, x)" in user
    assert user.count('"id": "gold_') == 1
    for value in ("complete corrected function", "no unified diff", "EXPLANATION:", "signature", "return type", "inside the corrected function", "Preserve normal behavior", "create new files"):
        assert value in system
    assert "```python" in user


@pytest.mark.parametrize("driver,placeholder", [("sqlite3", "?"), ("psycopg2", "%s"), ("mysql", "%s"), ("mysql.connector", "%s")])
def test_driver(driver, placeholder):
    assert f"Placeholder: {placeholder}" in build(db_driver=driver)[1]


@pytest.mark.parametrize("field", ["file", "line", "cwe", "severity", "rule_id", "language", "owasp"])
def test_missing_finding_field(field):
    value = finding()
    del value[field]
    with pytest.raises(ValueError):
        build(finding=value)


@pytest.mark.parametrize("changes", [dict(expected_behavior=""), dict(vulnerable_function=""), dict(db_driver=None), dict(driver_evidence=None), dict(db_driver="unknown"), dict(sql_present=False)])
def test_required_inputs(changes):
    with pytest.raises(ValueError):
        build(**changes)


@pytest.mark.parametrize("path", ["corpus/dev/sqli_01", "benchmark", "corpus/train/../../benchmark"])
def test_path_guard(path):
    with pytest.raises(ValueError, match="inside corpus/train"):
        build(example=path)


def test_symlink_guard(tmp_path):
    link = tmp_path / "outside"
    link.symlink_to(ROOT / "corpus/train/gold_sqli_01", target_is_directory=True)
    # An outside path resolving into train is safe; a train file resolving outside is not.
    from patcher import prompts
    root = tmp_path / "train"
    root.mkdir()
    (root / "meta.json").symlink_to(ROOT / "corpus/dev/sqli_01/meta.json")
    with patch.object(prompts, "TRAIN", root):
        with pytest.raises(ValueError, match="inside corpus/train"):
            load_example(root)


def test_c_prompt_and_selection():
    value = finding("c", "CWE-120")
    example = select_example(value)
    assert load_example(example)["language"] == "c"
    assert "#include" not in load_example(example)["repair"]
    assert "<string.h>" in load_example(example)["includes"]
    system, user = build_prompts(value, 'void f(char *s) { char b[8]; strcpy(b,s); }',
                                'Input: s="Bob"\nNormal result: copies Bob', None, example)
    assert "```c" in user
    assert "INCLUDES:" in system and "null termination" in system
    assert "not applicable" in user
    assert '"language": "c"' in user


@pytest.mark.parametrize("language", ["cpp", "Python", "", "javascript"])
def test_unsupported_language(language):
    with pytest.raises(ValueError, match="language"):
        build(finding=finding(language))


def test_cross_language_example_rejected():
    with pytest.raises(ValueError, match="language and CWE"):
        build(example="corpus/train/gold_bof_01")


def test_missing_same_language_examples(tmp_path):
    from patcher import prompts
    with patch.object(prompts, "TRAIN", tmp_path):
        with pytest.raises(ValueError, match="no example for language c"):
            select_example(finding("c", "CWE-120"))


def test_c_sql_requires_driver():
    with pytest.raises(ValueError, match="database driver"):
        build(finding=finding("c", "CWE-120"), vulnerable_function='void f() { run("SELECT x"); }',
              db_driver=None, example="corpus/train/gold_bof_01")


def test_runtime_config_transport_and_log(tmp_path):
    config = tmp_path / "model.yaml"
    config.write_text('model:\n  tag: "test-model:1"\n  temperature: 0.2\n')
    log = tmp_path / "calls.jsonl"
    raw = '```python\ndef f(x):\n    return x\n```\nEXPLANATION: Bound the value.'
    result = dict(model="test-model:1", done=True, message=dict(content=raw), eval_count=8)
    with patch("urllib.request.urlopen", return_value=io.BytesIO(json.dumps(result).encode())) as call:
        assert generate(finding(), "def f(x): return x", "Normal result: x", "sqlite3",
                        driver_evidence="caller: SQLite connection", config_path=config,
                        log_path=log, options=dict(seed=42, num_predict=256)) == raw
    payload = json.loads(call.call_args.args[0].data)
    assert [m["role"] for m in payload["messages"]] == ["system", "user"]
    assert payload["options"]["temperature"] == 0.2
    record = json.loads(log.read_text())
    for field in ("timestamp", "latency_seconds", "prompt_version", "language", "example_id", "model_tag", "temperature"):
        assert field in record
    assert record["raw_response"] == raw and record["eval_count"] == 8


def test_failed_call_logged(tmp_path):
    log = tmp_path / "calls.jsonl"
    with patch("urllib.request.urlopen", side_effect=TimeoutError("private URL")):
        with pytest.raises(TimeoutError):
            generate(finding("c", "CWE-120"), "void f() {}", "normal result", log_path=log)
    record = json.loads(log.read_text())
    assert record["status"] == "error" and record["error_type"] == "TimeoutError"
    assert "private URL" not in log.read_text()
