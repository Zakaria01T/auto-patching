# P5 Kaggle handoff

## Prepare private Kaggle inputs

1. Create a private Kaggle Dataset named `p5-dev-prompts`. Put the 32 exported files at `prompts/<case_id>.json` and `p5_kaggle_inference.py` at the dataset root. Use `model-compare/results/dev/calibration-7dc3da0513864a6ea41a63bac7573b2b/prompts/`; do not regenerate or edit those prompts.
2. Create a second private Dataset named `p5-adapters` with exactly these files and paths: `qlora/adapter_model.safetensors`, `qlora/adapter_config.json`, `rank32/adapter_model.safetensors`, and `rank32/adapter_config.json`. Do not include tokenizer files or the Dora adapter. The runner loads tokenizer and chat template from the pinned base revision, then verifies them against the recorded hashes.
3. Open `p5_kaggle_inference.ipynb` as a Kaggle Notebook and attach both datasets. Set **Accelerator: GPU T4 x2** and **Internet: On**. The notebook uses only GPU 0 (`device_map={"": 0}`); GPU 1 is not used for model sharding.
4. The notebook already sets the P6 values explicitly: `load_in_4bit=True`, `bnb_4bit_quant_type="nf4"`, `bnb_4bit_compute_dtype=torch.float16`, `bnb_4bit_use_double_quant=True`, `dtype=torch.float16`, and `device_map={"": 0}`. It pins base `Qwen/Qwen2.5-Coder-7B-Instruct` at `c03e6d358207e414f1eca0bb1891e29f1db0e242`, marked as an approximation because it was not recovered from training logs. No settings need filling for the run. Replace that revision only if you recover the original training commit, and then keep the same revision for all three models and re-freeze the config.
5. Run the notebook cells in order. First inspect the printed `p5_load_plan`: it must show repo commit `9792aad`, the approximate base revision and status, NF4/float16/double-quant values, GPU map `[0]`, and the expected adapter SHA-256 values. Then inspect each `loaded_model` line: baseline must have no adapter; qlora and rank32 must report `adapter_loaded: true`, their expected SHA-256, and `resolved_base_commit` equal to the requested revision. Stop and return the error if any digest, revision, tokenizer hash, or loaded device map fails validation. The notebook does not train and does not read repository source/test corpora. It writes `/kaggle/working/p5-results/p5-dev-generations.jsonl` and `manifest.json`.
6. Download exactly `p5-dev-generations.jsonl` and `manifest.json` from Kaggle and return them unchanged. Replay validates all 96 model/case rows, prompts, token hashes, adapter digests, generation settings, provenance labels and Docker environment.

The runner verifies adapter weight and config contents, including rank/alpha, dropout and the seven target modules. It checks tokenizer/chat-template hashes from the pinned base against the adapter provenance. The output includes raw function responses, exact system/user prompts, package versions, the actual resolved base commit, loaded adapter identity and device-map evidence. Qlora settings are labeled **assumed identical** because qlora ran in an earlier notebook version and its own artifacts do not record the NF4/model-load arguments; rank32 settings are **explicit in the supplied rank32 notebook code**. Generation is greedy (`do_sample=false`), seed 42, max 2048 new tokens, context 8192.

## Provenance checklist from the P6 training notebook

- Original Hugging Face model snapshot commit SHA actually used in training. The current shared evaluation revision is explicitly approximate, not recovered training provenance.
- qlora adapter artifacts confirm base model, rank 16, alpha 32, dropout 0.05, seven target modules, dataset commit/hash and package metadata. They do not prove NF4 compute dtype, double-quant, model dtype or device map; those are assumed identical to the shared rank32 cell and labeled accordingly.

## Output handoff

Return `p5-dev-generations.jsonl` and `manifest.json` to the evaluation owner. The Docker replay takes place separately on the repository host. If Kaggle stops before writing all 96 rows, report the error and return the partial output only for diagnosis; it is not an evaluation result.
