"""Dependency-free smoke/unit checks for the p5 converter and replay path."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

BASE = Path(__file__).resolve().parents[1]
ROOT = BASE.parent
sys.path.insert(0, str(BASE))

from evaluation import validate_patch
import replay
from p5_eval import build_case_prompts, function_response_to_diff


def replay_config():
    quant = {"load_in_4bit": True, "bnb_4bit_quant_type": "nf4", "bnb_4bit_compute_dtype": "float16", "bnb_4bit_use_double_quant": True}
    models = [
        {"type": "prompted", "tag": "hf-base", "checkpoint": "base@revision;nf4"},
        {"type": "fine-tuned", "tag": "hf-qlora", "checkpoint": "base@revision;nf4;qlora", "adapter_sha256": "a" * 64},
        {"type": "fine-tuned", "tag": "hf-rank32", "checkpoint": "base@revision;nf4;rank32", "adapter_sha256": "b" * 64},
    ]
    return {
        "models": models, "prompt_version": "p5-v1",
        "generation_parameters": {"temperature": 0.0, "seed": 42, "num_predict": 2048, "num_ctx": 8192},
        "inference_timeout": 180, "check_timeout": 180, "image": "sha256:" + "c" * 64,
        "memory": "1g", "cpus": 1, "pids_limit": 128,
        "ollama_url": "http://127.0.0.1:11434", "scanner_configuration": "project-original-v1",
        "inference_backend": "replay",
        "replay_metadata": {
            "base_model": "Qwen/Qwen2.5-Coder-7B-Instruct", "base_revision": "revision",
            "model_dtype": "float16", "device_map": {"": 0}, "gpu_devices_used": [0],
            "quantization": quant, "tokenizer_sha256": "d" * 64, "chat_template_sha256": "e" * 64,
        },
    }


def output_row(model, case_id, prompt, config):
    return {
        "case_id": case_id, "model_type": model["type"], "model_tag": model["tag"],
        "checkpoint_identity": model["checkpoint"], "base_model": "Qwen/Qwen2.5-Coder-7B-Instruct",
        "base_revision": "revision", "quantization": config["replay_metadata"]["quantization"],
        "base_revision_status": "verified",
        "model_dtype": config["replay_metadata"]["model_dtype"],
        "device_map": config["replay_metadata"]["device_map"],
        "gpu_devices_used": config["replay_metadata"]["gpu_devices_used"],
        "training_settings_provenance": model.get("training_settings_provenance", "unspecified"),
        "adapter_sha256": model.get("adapter_sha256"), "tokenizer_sha256": "d" * 64,
        "chat_template_sha256": "e" * 64, "prompt_version": "p5-v1",
        "generation_parameters": config["generation_parameters"],
        "decoding": {"do_sample": False, "max_new_tokens": 2048, "context_limit": 8192},
        "seed_applied": 42,
        "input_tokens": 128,
        "model_input_sha256": "f" * 64,
        "prompt": prompt, "prompt_sha256": replay._prompt_hash(prompt),
        "raw_output": "```python\ndef repair(x):\n    return x + 2\n```\nEXPLANATION: Returns a changed value.",
        "library_versions": {"transformers": "test", "peft": "test", "torch": "test", "bitsandbytes": "test"},
    }


class P5ReplayTests(unittest.TestCase):
    def test_gold_c_repairs_convert_and_pass_existing_p1_patch_validator(self):
        for case_id, target in (("gold_bof_01", "show_path"), ("gold_bof_02", "greet_user")):
            with self.subTest(case=case_id), tempfile.TemporaryDirectory() as tmp:
                folder = ROOT / "corpus/train" / case_id
                original = (folder / "vulnerable.c").read_text()
                repair = (folder / "repair.c").read_text()
                include_lines = [line for line in repair.splitlines() if line.lstrip().startswith("#include")]
                includes = ["<" + line.split("<", 1)[1].split(">", 1)[0] + ">" for line in include_lines]
                function = "\n".join(line for line in repair.splitlines() if not line.lstrip().startswith("#include")).strip()
                explanation = json.loads((folder / "meta.json").read_text())["explanation"]
                raw = f"```c\n{function}\n```\nEXPLANATION: {explanation}\nINCLUDES: {', '.join(includes)}"
                converted = function_response_to_diff(raw, original, "source.c", "c", target)
                self.assertTrue(converted["raw_format_valid"], converted["failure_reasons"])
                valid = validate_patch(converted["patch"], original, "source.c", "c", target, Path(tmp))
                self.assertTrue(valid["valid_output"], valid["failure_reasons"])
                self.assertTrue(valid["git_apply"])

    def test_bad_function_contract_is_rejected(self):
        original = "def repair(x):\n    return x + 1\n"
        cases = [
            ("--- a/source.py\n+++ b/source.py", "invalid_response_format"),
            ("```python\ndef repair(x, y):\n    return x\n```\nEXPLANATION: Changed signature.", "target function signature or decorators changed"),
            ("```python\ndef repair(x):\n    return x\n```\nEXPLANATION: Not C.\nINCLUDES: <stdio.h>", "INCLUDES is only permitted for C"),
        ]
        for raw, failure in cases:
            with self.subTest(failure=failure):
                result = function_response_to_diff(raw, original, "source.py", "python", "repair")
                self.assertFalse(result["raw_format_valid"])
                self.assertIn(failure, result["failure_reasons"])

    def test_replay_checks_prompts_and_runs_the_shared_evaluator(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            config = replay_config()
            config_path = tmp / "config.json"
            config_path.write_text(json.dumps(config))
            frozen_path = tmp / "frozen.json"
            case_dir = tmp / "case_1"
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
            input_path = tmp / "outputs.jsonl"
            rows = [output_row(model, "case_1", prompt, config) for model in config["models"]]
            input_path.write_text("".join(json.dumps(row) + "\n" for row in rows))

            environment = {"tools": {"test": "stub"}, "models": []}
            with patch.object(replay.harness, "code_hashes", return_value={"test.py": "hash"}), \
                 patch.object(replay, "load_cases", return_value=[case]), \
                 patch.object(replay.harness, "preflight", return_value=environment), \
                 patch.object(replay.harness, "check", side_effect=lambda _c, folder, mode: (
                     {"findings": [finding] if folder.resolve() == case_dir.resolve() else []} if mode == "scanner" else
                     {"passed": True, "reason": "ok"} if mode == "functional" else
                     {"passed": False, "reason": "attack_exploited"} if folder.resolve() == case_dir.resolve() else
                     {"passed": True, "reason": "attack_blocked"}
                 )):
                frozen_path.write_text(json.dumps({"config": config, "code_hashes": {"test.py": "hash"}, "environment": environment}))
                out = replay.run_replay(config_path, input_path, tmp / "results", frozen_path)

            records = [json.loads(line) for line in (out / "records.jsonl").read_text().splitlines()]
            self.assertEqual(len(records), 3)
            self.assertTrue(all(r["execution_status"] == "completed" for r in records))
            self.assertTrue(all(r["raw_format_valid"] and r["valid_output"] for r in records))
            self.assertTrue(all((out / r["raw_output_path"]).is_file() for r in records))
            self.assertEqual(len(list(out.rglob("prompt.json"))), 3)

    def test_saved_input_rejects_a_prompt_mismatch(self):
        config = replay_config()
        prompt = {"system": "system", "user": "user"}
        rows = [output_row(model, "case_1", prompt, config) for model in config["models"]]
        rows[-1]["prompt"] = {"system": "system", "user": "different prompt"}
        rows[-1]["prompt_sha256"] = replay._prompt_hash(rows[-1]["prompt"])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "outputs.jsonl"
            path.write_text("".join(json.dumps(row) + "\n" for row in rows))
            with self.assertRaisesRegex(replay.ReplayInputError, "prompts differ"):
                replay.load_replay_outputs(path, config, [{"id": "case_1"}])


if __name__ == "__main__":
    unittest.main()
