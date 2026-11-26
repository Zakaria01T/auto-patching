"""HF/PEFT inference runner invoked by p5_kaggle_inference.ipynb."""
from pathlib import Path
import hashlib
import importlib.metadata
import json
import platform
import time

import torch
from huggingface_hub import hf_hub_download
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, set_seed
from peft import PeftModel


def _sha256_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _prompt_hash(prompt):
    return hashlib.sha256(json.dumps(prompt, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def run_p5_inference(config):
    base_model = config["base_model"]
    base_revision = config["base_revision"]
    base_revision_status = config["base_revision_status"]
    base_revision_source = config["base_revision_source"]
    compute_dtype = config["nf4_compute_dtype"]
    double_quant = config["nf4_double_quant"]
    model_dtype = config["model_dtype"]
    device_map = config["device_map"]
    gpu_devices_used = config["gpu_devices_used"]
    prompt_dir = Path(config["prompt_dir"])
    qlora_dir = Path(config["qlora_adapter_dir"])
    rank32_dir = Path(config["rank32_adapter_dir"])
    output_dir = Path(config["output_dir"])
    seed, max_new_tokens, context_limit = 42, 2048, 8192
    tokenizer_sha = "3fd169731d2cbde95e10bf356d66d5997fd885dd8dbb6fb4684da3f23b2585d8"
    template_sha = "cd8e9439f0570856fd70470bf8889ebd8b5d1107207f67a5efb46e342330527f"
    adapter_shas = {
        "qlora": "eba7ae42144c22dd5302dbd908daf97f711568ec42a5dc9153d8ee75f646bd4e",
        "rank32": "44de96ea9de52f7373b17f3a66dc0506e8232e2b0e4abc357e751d23bb9f4661",
    }
    if (base_revision.startswith("REPLACE_") or base_revision_status not in ("verified", "approximation")
            or compute_dtype != "float16" or double_quant is not True or model_dtype != "float16"
            or device_map != {"": 0} or gpu_devices_used != [0]):
        raise ValueError("Supply the verified base revision, NF4 compute dtype, and double-quant setting")
    if not torch.cuda.is_available():
        raise RuntimeError("Kaggle GPU is required")
    if compute_dtype == "bfloat16" and not all(torch.cuda.is_bf16_supported(i) for i in range(torch.cuda.device_count())):
        raise RuntimeError("the selected NF4 bfloat16 compute dtype is unsupported by an attached GPU")
    prompt_paths = sorted(prompt_dir.glob("*.json"))
    if len(prompt_paths) != 32:
        raise ValueError(f"expected exactly 32 exported DEV prompts, found {len(prompt_paths)}")
    prompts = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in prompt_paths}
    if any(set(prompt) != {"system", "user"} for prompt in prompts.values()):
        raise ValueError("each prompt must contain exactly system and user strings")
    expected_lora = {
        "qlora": {"r": 16, "lora_alpha": 32},
        "rank32": {"r": 32, "lora_alpha": 64},
    }
    expected_targets = {"down_proj", "gate_proj", "k_proj", "o_proj", "q_proj", "up_proj", "v_proj"}
    adapter_config_hashes = {}
    for name, directory in (("qlora", qlora_dir), ("rank32", rank32_dir)):
        if _sha256_file(directory / "adapter_model.safetensors") != adapter_shas[name]:
            raise ValueError(f"{name} adapter SHA-256 mismatch")
        adapter_config = json.loads((directory / "adapter_config.json").read_text(encoding="utf-8"))
        if any(adapter_config.get(key) != value for key, value in expected_lora[name].items()):
            raise ValueError(f"{name} adapter_config.json rank/alpha mismatch")
        if adapter_config.get("lora_dropout") != 0.05 or set(adapter_config.get("target_modules", [])) != expected_targets:
            raise ValueError(f"{name} adapter_config.json dropout/target modules mismatch")
        adapter_config_hashes[name] = _sha256_file(directory / "adapter_config.json")

    quantization = {
        "load_in_4bit": True,
        "bnb_4bit_quant_type": "nf4",
        "bnb_4bit_compute_dtype": compute_dtype,
        "bnb_4bit_use_double_quant": double_quant,
    }
    model_specs = [
        ("prompted", "hf-qwen7b-nf4-base", None, None, f"{base_model}@{base_revision};quant=nf4", "evaluation settings explicitly matched to rank32 training code; prompted base has no adapter"),
        ("fine-tuned", "hf-qwen7b-nf4-qlora", "qlora", qlora_dir, f"{base_model}@{base_revision};adapter=qlora;quant=nf4", "assumed identical: shared training cell; qlora ran in an earlier notebook version; adapter files do not record NF4 compute dtype, double quant, model dtype, or device map"),
        ("fine-tuned", "hf-qwen7b-nf4-rank32", "rank32", rank32_dir, f"{base_model}@{base_revision};adapter=rank32;quant=nf4", "explicit in training notebook code (rank32 version, scriptVersionId 371928046)"),
    ]
    versions = {name: importlib.metadata.version(name) for name in ("torch", "transformers", "peft", "bitsandbytes", "accelerate", "safetensors")}
    gpu = [
        {"name": torch.cuda.get_device_name(i), "capability": torch.cuda.get_device_capability(i),
         "total_memory": torch.cuda.get_device_properties(i).total_memory}
        for i in range(torch.cuda.device_count())
    ]
    manifest = {
        "repo_commit": config["repo_commit"], "base_model": base_model, "base_revision": base_revision,
        "base_revision_status": base_revision_status, "base_revision_source": base_revision_source,
        "quantization": quantization, "model_dtype": model_dtype,
        "device_map": device_map, "gpu_devices_used": gpu_devices_used,
        "tokenizer_sha256": tokenizer_sha,
        "chat_template_sha256": template_sha,
        "adapters": {name: {"path": str(path), "adapter_model_sha256": _sha256_file(path / "adapter_model.safetensors")} for name, path in (("qlora", qlora_dir), ("rank32", rank32_dir))},
        "adapter_config_sha256": adapter_config_hashes,
        "training_settings_provenance": {tag: provenance for _, tag, _, _, _, provenance in model_specs},
        "generation_parameters": {"temperature": 0.0, "seed": seed, "num_predict": max_new_tokens, "num_ctx": context_limit},
        "decoding": {"do_sample": False, "max_new_tokens": max_new_tokens, "context_limit": context_limit},
        "gpu": gpu, "python": platform.python_version(), "library_versions": versions,
        "prompt_version": "p5-v1", "case_ids": sorted(prompts), "started_unix": time.time(),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    output_jsonl = output_dir / "p5-dev-generations.jsonl"
    manifest_path = output_dir / "manifest.json"
    output_jsonl.unlink(missing_ok=True)

    tokenizer_path = hf_hub_download(repo_id=base_model, filename="tokenizer.json", revision=base_revision)
    actual_tokenizer_sha = _sha256_file(tokenizer_path)
    tokenizer_config_path = hf_hub_download(repo_id=base_model, filename="tokenizer_config.json", revision=base_revision)
    tokenizer_config = json.loads(Path(tokenizer_config_path).read_text(encoding="utf-8"))
    template = tokenizer_config.get("chat_template")
    if isinstance(template, list):
        template = next((item.get("template") for item in template if item.get("name") == "default"), None)
    actual_template_sha = hashlib.sha256(template.encode("utf-8")).hexdigest() if isinstance(template, str) else None
    if actual_tokenizer_sha != tokenizer_sha or actual_template_sha != template_sha:
        raise ValueError("pinned base revision tokenizer/chat-template hashes differ from adapter provenance")
    tokenizer = AutoTokenizer.from_pretrained(base_model, revision=base_revision, use_fast=True)
    if tokenizer.eos_token_id is None:
        raise ValueError("tokenizer EOS token is required")
    manifest["resolved_tokenizer_sha256"] = actual_tokenizer_sha
    manifest["resolved_chat_template_sha256"] = actual_template_sha
    print(json.dumps({"p5_load_plan": {"repo_commit": config["repo_commit"], "base_model": base_model, "base_revision": base_revision, "base_revision_status": base_revision_status, "model_dtype": model_dtype, "device_map": device_map, "gpu_devices_used": gpu_devices_used, "quantization": quantization, "adapter_sha256": adapter_shas}}, indent=2), flush=True)

    for kind, tag, adapter_name, adapter_dir, checkpoint, settings_provenance in model_specs:
        set_seed(seed)
        bnb = BitsAndBytesConfig(
            load_in_4bit=True, bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=getattr(torch, compute_dtype),
            bnb_4bit_use_double_quant=double_quant,
        )
        model = AutoModelForCausalLM.from_pretrained(
            base_model, revision=base_revision, quantization_config=bnb,
            device_map=device_map, dtype=getattr(torch, model_dtype), low_cpu_mem_usage=True,
        )
        resolved_base_commit = getattr(model.config, "_commit_hash", None)
        if resolved_base_commit != base_revision:
            raise ValueError(f"loaded base commit {resolved_base_commit} differs from requested {base_revision}")
        if adapter_dir is not None:
            model = PeftModel.from_pretrained(model, adapter_dir, is_trainable=False)
        model.eval()
        actual_device_map = getattr(model, "hf_device_map", device_map)
        if any(device not in (0, "0") for device in actual_device_map.values()):
            raise RuntimeError(f"model sharded/offloaded outside GPU 0: {actual_device_map}")
        adapter_loaded = adapter_name is not None and hasattr(model, "peft_config")
        if (adapter_name is not None) != adapter_loaded:
            raise RuntimeError(f"adapter load state is wrong for {tag}")
        print(json.dumps({"loaded_model": tag, "base_model": base_model,
            "requested_base_revision": base_revision, "resolved_base_commit": resolved_base_commit,
            "base_revision_status": base_revision_status, "adapter": adapter_name,
            "adapter_sha256": adapter_shas.get(adapter_name), "adapter_loaded": adapter_loaded,
            "model_dtype": model_dtype, "device_map": actual_device_map,
            "training_settings_provenance": settings_provenance}, default=str), flush=True)
        for case_id in sorted(prompts):
            prompt = prompts[case_id]
            messages = [{"role": "system", "content": prompt["system"]}, {"role": "user", "content": prompt["user"]}]
            input_ids = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, return_tensors="pt")
            n_input = int(input_ids.shape[-1])
            if n_input + max_new_tokens > context_limit:
                raise ValueError(f"{case_id}: prompt plus generation limit exceeds context")
            input_ids = input_ids.to(model.get_input_embeddings().weight.device)
            token_hash = hashlib.sha256(input_ids.detach().cpu().numpy().astype("int64").tobytes()).hexdigest()
            with torch.inference_mode():
                generated = model.generate(input_ids=input_ids, do_sample=False, max_new_tokens=max_new_tokens, pad_token_id=tokenizer.eos_token_id)
            raw = tokenizer.decode(generated[0, n_input:], skip_special_tokens=True)
            row = {
                "case_id": case_id, "model_type": kind, "model_tag": tag, "checkpoint_identity": checkpoint,
                "base_model": base_model, "base_revision": base_revision,
                "base_revision_status": base_revision_status, "quantization": quantization,
                "adapter_sha256": adapter_shas[adapter_name] if adapter_name else None,
                "tokenizer_sha256": tokenizer_sha, "chat_template_sha256": template_sha,
                "model_dtype": model_dtype, "device_map": device_map,
                "gpu_devices_used": gpu_devices_used,
                "training_settings_provenance": settings_provenance,
                "prompt_version": "p5-v1", "generation_parameters": manifest["generation_parameters"],
                "decoding": manifest["decoding"], "seed_applied": seed, "input_tokens": n_input,
                "model_input_sha256": token_hash, "prompt": prompt, "prompt_sha256": _prompt_hash(prompt),
                "raw_output": raw, "library_versions": versions,
            }
            with output_jsonl.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(row, ensure_ascii=False) + "\n")
        del model, tokenizer
        torch.cuda.empty_cache()

    manifest["finished_unix"] = time.time()
    manifest["output_jsonl_sha256"] = _sha256_file(output_jsonl)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote {output_jsonl} and {manifest_path}")
    print(f"JSONL rows: {sum(1 for _ in output_jsonl.open(encoding='utf-8'))}")
