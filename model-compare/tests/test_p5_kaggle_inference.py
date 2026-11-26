import importlib.util
from pathlib import Path
import sys
from types import ModuleType
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parents[2]


class BatchEncodingLike(dict):
    """Minimal dict-shaped result returned by Transformers chat templates."""


def _load_runner_without_ml_dependencies():
    torch = ModuleType("torch")
    hub = ModuleType("huggingface_hub")
    hub.hf_hub_download = Mock()
    transformers = ModuleType("transformers")
    transformers.AutoModelForCausalLM = object
    transformers.AutoTokenizer = object
    transformers.BitsAndBytesConfig = object
    transformers.set_seed = Mock()
    peft = ModuleType("peft")
    peft.PeftModel = object
    spec = importlib.util.spec_from_file_location(
        "p5_kaggle_inference_under_test", ROOT / "model-compare/p5_kaggle_inference.py"
    )
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {
        "torch": torch,
        "huggingface_hub": hub,
        "transformers": transformers,
        "peft": peft,
    }):
        spec.loader.exec_module(module)
    return module


def test_chat_template_extracts_input_ids_from_batch_encoding_dict():
    runner = _load_runner_without_ml_dependencies()
    input_ids = object()
    encoded = BatchEncodingLike(input_ids=input_ids, attention_mask=object())
    tokenizer = Mock()
    tokenizer.apply_chat_template.return_value = encoded
    messages = [{"role": "user", "content": "hello"}]

    result = runner._encode_messages(tokenizer, messages)

    assert result is input_ids
    tokenizer.apply_chat_template.assert_called_once_with(
        messages,
        tokenize=True,
        add_generation_prompt=True,
        return_tensors="pt",
        return_dict=True,
    )


class FakeTokenIds:
    def __init__(self, values):
        self.values = values

    def detach(self):
        return self

    def cpu(self):
        return self

    def tolist(self):
        return self.values


def test_generation_finish_reason_counts_eos_and_token_limit():
    runner = _load_runner_without_ml_dependencies()

    assert runner._generation_finish_reason(FakeTokenIds([7, 2]), 2, 2048) == (2, "eos")
    assert runner._generation_finish_reason(FakeTokenIds([7, 8]), 2, 2) == (2, "max_new_tokens")
    assert runner._generation_finish_reason(FakeTokenIds([7]), 2, 2) == (1, "unknown")
