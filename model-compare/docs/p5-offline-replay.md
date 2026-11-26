# P5 HF/PEFT inference and offline P1 replay

## Why this path

The QLoRA adapters were trained on `Qwen/Qwen2.5-Coder-7B-Instruct` with a 4-bit
NF4 base. Running the baseline and both adapters through Hugging Face Transformers
and PEFT on the same pinned base revision and the same NF4 quantization avoids the
additional representation change that a merged GGUF export would introduce.
Greedy decoding (`do_sample=false`) and a fixed seed are recorded for all outputs.
This does not promise bitwise-identical GPU results across library or hardware
versions; the replay records those versions.

The alternative, merging each adapter and exporting all three checkpoints to
GGUF/Ollama, gives the existing P1 harness a native Ollama interface. It can also
make baseline fairness harder: GGUF quantization is not bitsandbytes NF4, and the
merge/export path may alter weights. Quantizing the baseline and both merged models
with the same GGUF recipe would align their inference representation with one
another, but not with the NF4 representation used to train the adapters. For this
task, the same-base/same-NF4 Hugging Face path is preferred.

Inference and sandbox replay are separate. Kaggle produces a JSONL file containing
one raw model response and the exact system/user prompts per DEV case and model.
First run P1 `calibrate-dev` with the frozen P5 replay config on a Docker-capable
CPU runner. On successful cases it writes `prompts/<case_id>.json` beside
`calibration.json`; transfer those prompt files to Kaggle and use them unchanged
for the base and both adapters. The offline runner rebuilds the prompts locally, checks them byte-for-byte against
the saved prompts, and routes the saved response through the P1 validation,
functional, attack, and scanner checks. Those checks still require Docker on the
replay host; inference does not. `model-compare/replay.py` is DEV-only and never
loads `benchmark/`.

## Prompt and metric boundary

`p5-v1` is built by `patcher.prompts.build_prompts()`. All three models receive the
same messages, including the selected original finding, expected behavior, DB
context where applicable, and one same-language/same-CWE train example. The HF
runner must preserve these messages and the shared chat template in its JSONL.

The strict converter accepts one complete corrected function in the expected
language fence, one explanation line, and (for C) an optional list of approved
standard headers. It rejects extra prose, multiple functions, a changed function
signature, unapproved headers, and malformed responses. It creates a unified diff
for the existing P1 patch validator. The five P1 formulas and denominators do not
change, but the valid-output decision is made after this I/O adapter. P1 originally
judged the raw output as a unified diff, so this is a documented methodological
extension. Reports keep raw-format compliance separate from the five P1 metrics;
raw responses, exact prompts, and converted diffs are retained.

## Replay JSONL contract

`p5-replay-input.example.jsonl` shows the required per-case fields. The real input
must include exactly one row for every model/case pair in `corpus/dev/`. Each row
records model type/tag/checkpoint identity, base model and revision, complete NF4
configuration, adapter SHA-256 (null for the prompted base), tokenizer and chat
template hashes, prompt version, generation settings, exact system/user strings,
prompt SHA-256, chat-template token ID hash and input token count, applied seed,
raw response, and inference package versions. Replay rejects mismatched prompts or
token IDs and any prompt whose input plus `max_new_tokens` exceeds the frozen
context limit.

The replay config pins the Docker image ID, all three model identities, generation
settings, base revision, quantization parameters, tokenizer hash, and chat-template
hash. The checked-in example pins the Docker image and records base revision
`c03e6d358207e414f1eca0bb1891e29f1db0e242` as an approximation from Hugging Face
history, not as the recovered training revision. It remains non-runnable until
the NF4 compute/double-quant settings are confirmed. If the training code omits
these arguments, Transformers 5.20.2 resolves compute dtype to `torch.float32`
and double quantization to `False`; this is conditional on confirming the
omissions in the actual notebook block.

After the inference host and Docker replay host are available, the flow is:

```bash
python3 model-compare/run.py check-dev
docker build -f model-compare/Dockerfile -t repair-eval:p5 .
docker image inspect repair-eval:p5 --format '{{.Id}}'
python3 model-compare/run.py freeze --config model-compare/config.p5-replay.local.json --frozen model-compare/p5-replay.frozen.json
python3 model-compare/run.py calibrate-dev --config model-compare/config.p5-replay.local.json --output-dir model-compare/results
python3 model-compare/replay.py --config model-compare/config.p5-replay.local.json --frozen model-compare/p5-replay.frozen.json --input-jsonl /path/to/kaggle-dev-outputs.jsonl --output-dir model-compare/results
```

Do not run these commands until the remaining provenance and execution inputs are
resolved and the evaluation owner approves Phase 3 execution.

## Calibration fixture availability

`corpus/dev/` contains vulnerable sources, reviewed specs, and tests; it has no
gold `repair.c` files. The converter unit tests therefore use the two committed C
gold repairs under `corpus/train/gold_bof_01/` and `corpus/train/gold_bof_02/` to
exercise conversion and the P1 patch validator. This proves format conversion and
patch acceptance only. A real P1 fix calibration (normal test, exploit, and
scanner checks) still requires the Docker sandbox and must be completed before
model replay.
