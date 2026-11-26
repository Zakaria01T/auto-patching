import hashlib
import json
from pathlib import Path
import sys

import pytest

BASE = Path(__file__).resolve().parents[1]
ROOT = BASE.parent
sys.path.insert(0, str(BASE))

import replay
from p5_eval import build_case_prompts


def _config():
    quant = {
        "load_in_4bit": True,
        "bnb_4bit_quant_type": "nf4",
        "bnb_4bit_compute_dtype": "float16",
        "bnb_4bit_use_double_quant": True,
    }
    models = [
        {"type": "prompted", "tag": "hf-base", "checkpoint": "base@revision;nf4"},
        {"type": "fine-tuned", "tag": "hf-qlora", "checkpoint": "base@revision;nf4;qlora", "adapter_sha256": "a" * 64},
        {"type": "fine-tuned", "tag": "hf-rank32", "checkpoint": "base@revision;nf4;rank32", "adapter_sha256": "b" * 64},
    ]
    return {
        "models": models,
        "prompt_version": "p5-v1",
        "generation_parameters": {"temperature": 0.0, "seed": 42, "num_predict": 2048, "num_ctx": 8192},
        "inference_timeout": 180,
        "check_timeout": 180,
        "image": "sha256:" + "c" * 64,
        "memory": "1g",
        "cpus": 1,
        "pids_limit": 128,
        "ollama_url": "http://127.0.0.1:11434",
        "scanner_configuration": "project-original-v1",
        "inference_backend": "replay",
        "replay_metadata": {
            "base_model": "Qwen/Qwen2.5-Coder-7B-Instruct",
            "base_revision": "revision",
            "model_dtype": "float16",
            "device_map": {"": 0},
            "gpu_devices_used": [0],
            "quantization": quant,
            "tokenizer_sha256": "d" * 64,
            "chat_template_sha256": "e" * 64,
        },
    }


def _row(model, case_id, prompt, generation, quant):
    return {
        "case_id": case_id,
        "model_type": model["type"],
        "model_tag": model["tag"],
        "checkpoint_identity": model["checkpoint"],
        "base_model": "Qwen/Qwen2.5-Coder-7B-Instruct",
        "base_revision": "revision",
        "base_revision_status": "verified",
        "model_dtype": "float16",
        "device_map": {"": 0},
        "gpu_devices_used": [0],
        "training_settings_provenance": "unspecified",
        "quantization": quant,
        "adapter_sha256": model.get("adapter_sha256"),
        "tokenizer_sha256": "d" * 64,
        "chat_template_sha256": "e" * 64,
        "prompt_version": "p5-v1",
        "generation_parameters": generation,
        "decoding": {"do_sample": False, "max_new_tokens": 2048, "context_limit": 8192},
        "seed_applied": 42,
        "input_tokens": 128,
        "model_input_sha256": "f" * 64,
        "prompt": prompt,
        "prompt_sha256": replay._prompt_hash(prompt),
        "raw_output": "```python\ndef repair(x):\n    return x + 2\n```\nEXPLANATION: Returns a changed value.",
        "library_versions": {"transformers": "test", "peft": "test", "torch": "test", "bitsandbytes": "test"},
    }


def test_replay_input_requires_complete_identical_three_model_matrix(tmp_path):
    config = _config()
    case = {"id": "case_1"}
    prompt = {"system": "system", "user": "user"}
    rows = [_row(model, "case_1", prompt, config["generation_parameters"], config["replay_metadata"]["quantization"]) for model in config["models"]]
    source = tmp_path / "outputs.jsonl"
    source.write_text("".join(json.dumps(row) + "\n" for row in rows))
    parsed, versions = replay.load_replay_outputs(source, config, [case])
    assert set(parsed) == {(model["tag"], "case_1") for model in config["models"]}
    assert versions["transformers"] == "test"

    rows[-1]["prompt"] = {"system": "system", "user": "different user prompt"}
    rows[-1]["prompt_sha256"] = replay._prompt_hash(rows[-1]["prompt"])
    source.write_text("".join(json.dumps(row) + "\n" for row in rows))
    with pytest.raises(replay.ReplayInputError, match="prompts differ"):
        replay.load_replay_outputs(source, config, [case])


def test_replay_executes_shared_evaluator_without_model_or_docker(monkeypatch, tmp_path):
    """MOCK ONLY: one synthetic case x three model rows; never a P5 result."""
    config = _config()
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config))
    case_dir = tmp_path / "case_1"
    case_dir.mkdir()
    source = case_dir / "source.py"
    source.write_text("def repair(x):\n    return x + 1\n")
    test_file = case_dir / "test.txt"
    test_file.write_text("repair(1) returns 2\n")
    spec_file = case_dir / "evaluation.json"
    spec_file.write_text(json.dumps({"class": "command_injection", "scenario": 1, "target": "repair", "test_sha256": hashlib.sha256(test_file.read_bytes()).hexdigest()}))
    (case_dir / "meta.json").write_text(json.dumps({"id": "case_1", "language": "python", "class": "command_injection", "cwe": "CWE-78"}))
    case = {"id": "case_1", "language": "python", "class": "command_injection", "cwe": "CWE-78", "source": source, "test": test_file, "spec": spec_file}
    finding = {"file": "source.py", "line": 1, "cwe": "CWE-78", "severity": "high", "rule_id": "cmdi-test", "language": "python", "owasp": "A03:2021-Injection"}
    prompt, _ = build_case_prompts(case, source.read_text(), [finding], "repair")
    input_path = tmp_path / "outputs.jsonl"
    rows = [_row(model, "case_1", prompt, config["generation_parameters"], config["replay_metadata"]["quantization"]) for model in config["models"]]
    input_path.write_text("".join(json.dumps(row) + "\n" for row in rows))

    monkeypatch.setattr(replay, "load_cases", lambda split: [case])
    monkeypatch.setattr(replay.harness, "preflight", lambda *args, **kwargs: {"tools": {"test": "stub"}, "models": []})

    def fake_check(_config, folder, mode):
        if mode == "scanner":
            findings = [finding] if folder.resolve() == case_dir.resolve() else []
            return {"findings": findings}
        if mode == "functional":
            return {"passed": True, "reason": "ok"}
        if folder.resolve() == case_dir.resolve():
            return {"passed": False, "reason": "attack_exploited"}
        return {"passed": True, "reason": "attack_blocked"}

    monkeypatch.setattr(replay.harness, "check", fake_check)
    environment = {"tools": {"test": "stub"}, "models": []}
    frozen_path = tmp_path / "frozen.json"
    monkeypatch.setattr(replay.harness, "code_hashes", lambda: {"test.py": "hash"})
    frozen_path.write_text(json.dumps({"config": config, "code_hashes": {"test.py": "hash"}, "environment": environment}))
    out = replay.run_replay(config_path, input_path, tmp_path / "results", frozen_path)
    records = [json.loads(line) for line in (out / "records.jsonl").read_text().splitlines()]
    assert len(records) == 3
    assert all(record["execution_status"] == "completed" for record in records)
    assert all(record["raw_format_valid"] and record["valid_output"] for record in records)
    assert all((out / record["raw_output_path"]).is_file() for record in records)
    assert len(list(out.rglob("prompt.json"))) == 3

