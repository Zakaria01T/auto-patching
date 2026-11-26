import difflib
import json
from pathlib import Path
import sys

import pytest

BASE = Path(__file__).resolve().parents[1]
ROOT = BASE.parent
sys.path.insert(0, str(BASE))

from evaluation import validate_patch
from p5_eval import build_case_prompts, function_response_to_diff


@pytest.mark.parametrize(
    "case_id,target",
    [("gold_bof_01", "show_path"), ("gold_bof_02", "greet_user")],
)
def test_gold_c_function_to_diff_and_existing_validator(case_id, target, tmp_path):
    folder = ROOT / "corpus/train" / case_id
    original = (folder / "vulnerable.c").read_text()
    repaired = (folder / "repair.c").read_text()
    includes = []
    function_lines = []
    for line in repaired.splitlines():
        if line.lstrip().startswith("#include"):
            header = line.split("<", 1)[1].split(">", 1)[0]
            includes.append(f"<{header}>")
        else:
            function_lines.append(line)
    function_code = "\n".join(function_lines).strip()
    explanation = json.loads((folder / 'meta.json').read_text())["explanation"]
    raw = f"```c\n{function_code}\n```\nEXPLANATION: {explanation}\nINCLUDES: {', '.join(includes)}"

    converted = function_response_to_diff(raw, original, "source.c", "c", target)
    assert converted["raw_format_valid"]
    checked = validate_patch(converted["patch"], original, "source.c", "c", target, tmp_path)
    assert checked["valid_output"] and checked["git_apply"]


def test_python_response_replaces_only_named_function():
    original = "import os\n\ndef repair(x):\n    return x + 1\n\ndef keep():\n    return 5\n"
    raw = "```python\ndef repair(x):\n    return x + 2\n```\nEXPLANATION: Changes the result safely."
    converted = function_response_to_diff(raw, original, "source.py", "python", "repair")
    assert converted["raw_format_valid"]
    assert "def keep():\n    return 5" in converted["patched_source"]
    assert "return x + 2" in converted["patched_source"]


@pytest.mark.parametrize(
    "raw,reason",
    [
        ("--- a/source.py\n+++ b/source.py", "invalid_response_format"),
        ("```python\ndef other(x):\n    return x\n```\nEXPLANATION: Wrong target.", "target function is missing or duplicated"),
        ("```python\ndef repair(x, y):\n    return x\n```\nEXPLANATION: Signature changed.", "target function signature or decorators changed"),
        ("```python\ndef repair(x):\n    return x\n```\nEXPLANATION: No fix.\nINCLUDES: <stdio.h>", "INCLUDES is only permitted for C"),
        ("```c\nvoid repair(void) {}\n```\nEXPLANATION: Fix.\nINCLUDES: <unistd.h>", "INCLUDES contains a non-approved standard header"),
    ],
)
def test_malformed_or_contract_breaking_response_is_rejected(raw, reason):
    original = "def repair(x):\n    return x + 1\n"
    language = "c" if "```c" in raw else "python"
    source = "void repair(void) { return; }\n" if language == "c" else original
    result = function_response_to_diff(raw, source, "source." + ("c" if language == "c" else "py"), language, "repair")
    assert not result["raw_format_valid"]
    assert reason in result["failure_reasons"]


def test_p5_case_prompt_uses_production_builder_and_train_example():
    source = ROOT / "corpus/dev/bof_01/source.c"
    case = {
        "id": "bof_01", "language": "c", "class": "buffer_overflow", "cwe": "CWE-120",
        "source": source, "test": ROOT / "corpus/dev/bof_01/test.txt",
    }
    finding = {
        "file": "source.c", "line": 5, "cwe": "CWE-120", "severity": "high",
        "rule_id": "example-c-rule", "language": "c", "owasp": "A03:2021-Injection",
    }
    messages, provenance = build_case_prompts(case, source.read_text(), [finding], "copy_name")
    assert "complete corrected function" in messages["system"]
    assert "Exactly one same-language example" in messages["user"]
    assert provenance["example"].startswith("corpus/train/")

