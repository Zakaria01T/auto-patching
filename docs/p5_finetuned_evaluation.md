# P5: Fine-tuned model evaluation against prompted model

**Status:** Completed using archived Kaggle run1 generations. Strict format mode is the primary result; lenient format mode is a separate sensitivity analysis. The supervisor accepted using run1 rather than rerunning Kaggle.

## Summary and recommendation

Under required **strict primary mode**, prompted baseline Fix Rate is **23/32 (71.875%)**. Adapter A is **29/32 (90.625%)**, and adapter B is **28/32 (87.500%)**. Both adapters beat the baseline on DEV strict Fix Rate and satisfy the recommendation rule. A exceeds B by one case; with only 32 cases this is descriptive, not a significance claim.

The **lenient sensitivity analysis changes the conclusion**: baseline is **30/32 (93.750%)**, A **29/32 (90.625%)**, B **28/32 (87.500%)**. Neither adapter beats baseline in lenient mode. Strict is primary because p5-v1 requires imports inside Python function and C headers through `INCLUDES:`; lenient is separate and never pooled.

No results here estimate performance on `benchmark/` or the sealed benchmark.

## Setup and reproducibility

- Dataset: `corpus/dev/`, exactly 32 case IDs (8 per class), all three conditions (96 rows per run). Both run manifests say `dataset_split=dev`; replay loads only DEV. No benchmark/test cases were used.
- Input JSONL is archived at [`model-compare/results/p5-run1-input/p5-dev-generations.jsonl`](../model-compare/results/p5-run1-input/p5-dev-generations.jsonl), SHA-256 `4b4a35b1694f824aab3a8cd76b30072ff29c1c819f7cd07e330055da63b1051b`. Input manifest [`manifest.json`](../model-compare/results/p5-run1-input/manifest.json) SHA-256 `c324496772f15a34c5713abf8511aceb1e7d066ee71182514e8a36be3e2f8048`.
- The input checks validate the same 32 IDs × 3 tags, JSONL digest, adapter SHA-256, p5-v1, prompt hashes, tokenized-input hashes, tokenizer/template hashes, generation, and NF4 fields. Prompts and tokenized inputs match across all three models per case.
- Prompt and generation: `p5-v1`; greedy (`do_sample=false`); temperature `0.0`; seed `42`; max new tokens `2048`; context `8192`.
- Base: `Qwen/Qwen2.5-Coder-7B-Instruct`, revision `c03e6d358207e414f1eca0bb1891e29f1db0e242`, marked **approximation**, not a verified training revision. Recorded inference NF4: 4-bit, `nf4`, compute dtype `float16`, double quantization `true`.
- Models: prompted baseline `hf-qwen7b-nf4-base`; A `hf-qwen7b-nf4-qlora` rank 16 / alpha 32, adapter SHA-256 `eba7ae42144c22dd5302dbd908daf97f711568ec42a5dc9153d8ee75f646bd4e`; B `hf-qwen7b-nf4-rank32` rank 32 / alpha 64, adapter SHA-256 `44de96ea9de52f7373b17f3a66dc0506e8232e2b0e4abc357e751d23bb9f4661`.
- The Kaggle runner that actually ran was the earlier patched file, SHA-256 `0fd47ed6030ec12002d728fc422ef12f2777e81628234fd60918031d21a75596`; it differs from the repo runner. It ran with `device_map=auto` in the Kaggle T4 × 2 environment; actual GPU placement is not recorded.
- Freeze: [`config.p5-replay.run1.json`](../model-compare/config.p5-replay.run1.json) and [`p5-replay-run1-converter-v3.frozen.json`](../model-compare/p5-replay-run1-converter-v3.frozen.json), SHA-256 `2ffa9206cd68603aba14c231dc3ae8017d9af0810d54e22bf7454d2bf19a1510`. V3 was required because lenient converter code changed; rules were documented before replay. Strict was rerun under v3 and matched the saved strict run exactly per case.
- Docker image: `sha256:d8f383761b89b139aae56746d82011abcf84f72bc3c1176c368336c22802ddf4`. Versions recorded: torch `2.11.0+cu130`, transformers `5.20.2`, peft `0.21.2`, bitsandbytes `0.50.2`, accelerate `1.15.0`, safetensors `0.8.0`.
- Run IDs: strict primary `20261126T050228-38b4cf5e9834`; lenient secondary `20261126T044828-863c151ddad5`; both use the v3 freeze. Earlier strict run `20261126T041800-3ac176330422` has identical strict format outcomes, exact converted diffs, and P1 metric booleans.
- Replay commands (Docker image must already exist):

```bash
/tmp/p5-test-venv/bin/python model-compare/replay.py --config model-compare/config.p5-replay.run1.json --input-jsonl model-compare/results/p5-run1-input/p5-dev-generations.jsonl --input-manifest model-compare/results/p5-run1-input/manifest.json --frozen model-compare/p5-replay-run1-converter-v3.frozen.json --output-dir model-compare/results --legacy-manifest --format-mode strict
/tmp/p5-test-venv/bin/python model-compare/replay.py --config model-compare/config.p5-replay.run1.json --input-jsonl model-compare/results/p5-run1-input/p5-dev-generations.jsonl --input-manifest model-compare/results/p5-run1-input/manifest.json --frozen model-compare/p5-replay-run1-converter-v3.frozen.json --output-dir model-compare/results --legacy-manifest --format-mode lenient
```

Actual invocations read `/home/chekraoui/p5-kaggle-output-run1/`; committed copies have the same verified hashes. Complete per-case raw outputs, prompts, diffs, records, summaries, and manifests are in the run folders under [`model-compare/results/dev/`](../model-compare/results/dev/).

### Legacy provenance

Legacy mode was explicitly enabled for run1 only; normal strict manifest validation remains unchanged. Per-row `base_revision_status`, actual `gpu_devices_used`, `model_dtype`, `training_settings_provenance`, generated token count, and finish reason are **NOT RECORDED**. `device_map=auto` is known as a runner setting; actual device placement is not recorded. Truncation at 2048 tokens cannot be measured. The frozen config labels the base revision as an approximation; that status was not recorded in legacy rows.

### Metric and converter definitions

P1 denominators include all assigned cases. Overall uses pooled case counts. Valid Output Rate is valid P1 patch / total; Functional Test Pass Rate is normal checks passed / total; Attack Blocked Rate is attack checks blocked / total; Scanner Rate is original CWE/rule findings cleared / total; Fix Rate is exactly `valid_output AND functional_test_pass AND attack_blocked`. Scanner clearance is independent of Fix Rate. Format-rejected outputs stay in denominators and skipped checks are not passes.

Strict mode accepts one target function in the language fence, an explanation, and optional C headers through `INCLUDES:`. Blank separator lines are tolerated because p5-v1 describes separate lines without forbidding blank separators. Strict rejects top-level Python imports, fenced C `#include`, unapproved headers, extra code, and malformed fences. Lenient mode additionally moves unambiguous top-level Python imports into the function and extracts approved fenced C headers. The frozen strict/lenient rules are in [`p5-offline-replay.md`](../model-compare/docs/p5-offline-replay.md). Function-to-diff conversion is a documented extension to P1, which originally consumed unified diffs. Each mode has a separate run; the aggregator rejects mixed modes.

## Strict results (primary)

| Model | Valid output | Functional test pass | Attack blocked | Scanner cleared | Fix |
|---|---:|---:|---:|---:|---:|
| Prompted baseline (no adapter) | 23/32 (71.875%) | 23/32 (71.875%) | 23/32 (71.875%) | 19/32 (59.375%) | 23/32 (71.875%) |
| A: QLoRA (rank 16, alpha 32) | 31/32 (96.875%) | 29/32 (90.625%) | 31/32 (96.875%) | 29/32 (90.625%) | 29/32 (90.625%) |
| B: QLoRA (rank 32, alpha 64) | 31/32 (96.875%) | 29/32 (90.625%) | 30/32 (93.750%) | 29/32 (90.625%) | 28/32 (87.500%) |

### Strict per-class metrics

| Vulnerability class | Model | Valid output | Functional test pass | Attack blocked | Scanner cleared | Fix |
|---|---|---:|---:|---:|---:|---:|
| Buffer overflow | Prompted baseline (no adapter) | 8/8 (100.000%) | 8/8 (100.000%) | 8/8 (100.000%) | 4/8 (50.000%) | 8/8 (100.000%) |
| Buffer overflow | A: QLoRA (rank 16, alpha 32) | 7/8 (87.500%) | 7/8 (87.500%) | 7/8 (87.500%) | 5/8 (62.500%) | 7/8 (87.500%) |
| Buffer overflow | B: QLoRA (rank 32, alpha 64) | 7/8 (87.500%) | 7/8 (87.500%) | 6/8 (75.000%) | 5/8 (62.500%) | 6/8 (75.000%) |
| Command injection | Prompted baseline (no adapter) | 0/8 (0.000%) | 0/8 (0.000%) | 0/8 (0.000%) | 0/8 (0.000%) | 0/8 (0.000%) |
| Command injection | A: QLoRA (rank 16, alpha 32) | 8/8 (100.000%) | 6/8 (75.000%) | 8/8 (100.000%) | 8/8 (100.000%) | 6/8 (75.000%) |
| Command injection | B: QLoRA (rank 32, alpha 64) | 8/8 (100.000%) | 6/8 (75.000%) | 8/8 (100.000%) | 8/8 (100.000%) | 6/8 (75.000%) |
| SQL injection | Prompted baseline (no adapter) | 7/8 (87.500%) | 7/8 (87.500%) | 7/8 (87.500%) | 7/8 (87.500%) | 7/8 (87.500%) |
| SQL injection | A: QLoRA (rank 16, alpha 32) | 8/8 (100.000%) | 8/8 (100.000%) | 8/8 (100.000%) | 8/8 (100.000%) | 8/8 (100.000%) |
| SQL injection | B: QLoRA (rank 32, alpha 64) | 8/8 (100.000%) | 8/8 (100.000%) | 8/8 (100.000%) | 8/8 (100.000%) | 8/8 (100.000%) |
| XSS | Prompted baseline (no adapter) | 8/8 (100.000%) | 8/8 (100.000%) | 8/8 (100.000%) | 8/8 (100.000%) | 8/8 (100.000%) |
| XSS | A: QLoRA (rank 16, alpha 32) | 8/8 (100.000%) | 8/8 (100.000%) | 8/8 (100.000%) | 8/8 (100.000%) | 8/8 (100.000%) |
| XSS | B: QLoRA (rank 32, alpha 64) | 8/8 (100.000%) | 8/8 (100.000%) | 8/8 (100.000%) | 8/8 (100.000%) | 8/8 (100.000%) |

### Strict raw-format compliance

| Model | Accepted | Rejected | Rejected case IDs |
|---|---:|---:|---|
| Prompted baseline (no adapter) | 23/32 (71.875%) | 9/32 (28.125%) | cmdi_01, cmdi_02, cmdi_03, cmdi_04, cmdi_05, cmdi_06, cmdi_07, cmdi_08, sqli_07 |
| A: QLoRA (rank 16, alpha 32) | 31/32 (96.875%) | 1/32 (3.125%) | bof_04 |
| B: QLoRA (rank 32, alpha 64) | 31/32 (96.875%) | 1/32 (3.125%) | bof_04 |

Strict converter rejections by class (count, denominator 8):

| Model | BOF | Command injection | SQL injection | XSS |
|---|---:|---:|---:|---:|
| Prompted baseline (no adapter) | 0 | 8 | 1 | 0 |
| A: QLoRA (rank 16, alpha 32) | 1 | 0 | 0 | 0 |
| B: QLoRA (rank 32, alpha 64) | 1 | 0 | 0 | 0 |

### Strict successful and failed repairs

Successful/failed means the P1 Fix definition. Scanner-only failures can still be successful repairs.

| Model | Successful case IDs | Failed case IDs |
|---|---|---|
| Prompted baseline (no adapter) | bof_01, bof_02, bof_03, bof_04, bof_05, bof_06, bof_07, bof_08, sqli_01, sqli_02, sqli_03, sqli_04, sqli_05, sqli_06, sqli_08, xss_01, xss_02, xss_03, xss_04, xss_05, xss_06, xss_07, xss_08 | cmdi_01, cmdi_02, cmdi_03, cmdi_04, cmdi_05, cmdi_06, cmdi_07, cmdi_08, sqli_07 |
| A: QLoRA (rank 16, alpha 32) | bof_01, bof_02, bof_03, bof_05, bof_06, bof_07, bof_08, cmdi_01, cmdi_02, cmdi_04, cmdi_06, cmdi_07, cmdi_08, sqli_01, sqli_02, sqli_03, sqli_04, sqli_05, sqli_06, sqli_07, sqli_08, xss_01, xss_02, xss_03, xss_04, xss_05, xss_06, xss_07, xss_08 | bof_04, cmdi_03, cmdi_05 |
| B: QLoRA (rank 32, alpha 64) | bof_01, bof_02, bof_03, bof_05, bof_06, bof_07, cmdi_01, cmdi_02, cmdi_03, cmdi_06, cmdi_07, cmdi_08, sqli_01, sqli_02, sqli_03, sqli_04, sqli_05, sqli_06, sqli_07, sqli_08, xss_01, xss_02, xss_03, xss_04, xss_05, xss_06, xss_07, xss_08 | bof_04, bof_08, cmdi_04, cmdi_05 |

## Lenient sensitivity analysis (secondary; separate results)

| Model | Valid output | Functional test pass | Attack blocked | Scanner cleared | Fix |
|---|---:|---:|---:|---:|---:|
| Prompted baseline (no adapter) | 31/32 (96.875%) | 31/32 (96.875%) | 30/32 (93.750%) | 26/32 (81.250%) | 30/32 (93.750%) |
| A: QLoRA (rank 16, alpha 32) | 31/32 (96.875%) | 29/32 (90.625%) | 31/32 (96.875%) | 29/32 (90.625%) | 29/32 (90.625%) |
| B: QLoRA (rank 32, alpha 64) | 31/32 (96.875%) | 29/32 (90.625%) | 30/32 (93.750%) | 29/32 (90.625%) | 28/32 (87.500%) |

### Lenient per-class metrics

| Vulnerability class | Model | Valid output | Functional test pass | Attack blocked | Scanner cleared | Fix |
|---|---|---:|---:|---:|---:|---:|
| Buffer overflow | Prompted baseline (no adapter) | 8/8 (100.000%) | 8/8 (100.000%) | 8/8 (100.000%) | 4/8 (50.000%) | 8/8 (100.000%) |
| Buffer overflow | A: QLoRA (rank 16, alpha 32) | 7/8 (87.500%) | 7/8 (87.500%) | 7/8 (87.500%) | 5/8 (62.500%) | 7/8 (87.500%) |
| Buffer overflow | B: QLoRA (rank 32, alpha 64) | 7/8 (87.500%) | 7/8 (87.500%) | 6/8 (75.000%) | 5/8 (62.500%) | 6/8 (75.000%) |
| Command injection | Prompted baseline (no adapter) | 8/8 (100.000%) | 8/8 (100.000%) | 7/8 (87.500%) | 7/8 (87.500%) | 7/8 (87.500%) |
| Command injection | A: QLoRA (rank 16, alpha 32) | 8/8 (100.000%) | 6/8 (75.000%) | 8/8 (100.000%) | 8/8 (100.000%) | 6/8 (75.000%) |
| Command injection | B: QLoRA (rank 32, alpha 64) | 8/8 (100.000%) | 6/8 (75.000%) | 8/8 (100.000%) | 8/8 (100.000%) | 6/8 (75.000%) |
| SQL injection | Prompted baseline (no adapter) | 7/8 (87.500%) | 7/8 (87.500%) | 7/8 (87.500%) | 7/8 (87.500%) | 7/8 (87.500%) |
| SQL injection | A: QLoRA (rank 16, alpha 32) | 8/8 (100.000%) | 8/8 (100.000%) | 8/8 (100.000%) | 8/8 (100.000%) | 8/8 (100.000%) |
| SQL injection | B: QLoRA (rank 32, alpha 64) | 8/8 (100.000%) | 8/8 (100.000%) | 8/8 (100.000%) | 8/8 (100.000%) | 8/8 (100.000%) |
| XSS | Prompted baseline (no adapter) | 8/8 (100.000%) | 8/8 (100.000%) | 8/8 (100.000%) | 8/8 (100.000%) | 8/8 (100.000%) |
| XSS | A: QLoRA (rank 16, alpha 32) | 8/8 (100.000%) | 8/8 (100.000%) | 8/8 (100.000%) | 8/8 (100.000%) | 8/8 (100.000%) |
| XSS | B: QLoRA (rank 32, alpha 64) | 8/8 (100.000%) | 8/8 (100.000%) | 8/8 (100.000%) | 8/8 (100.000%) | 8/8 (100.000%) |

### Lenient raw-format compliance

| Model | Accepted | Rejected | Rejected case IDs |
|---|---:|---:|---|
| Prompted baseline (no adapter) | 31/32 (96.875%) | 1/32 (3.125%) | sqli_07 |
| A: QLoRA (rank 16, alpha 32) | 31/32 (96.875%) | 1/32 (3.125%) | bof_04 |
| B: QLoRA (rank 32, alpha 64) | 31/32 (96.875%) | 1/32 (3.125%) | bof_04 |

Lenient converter rejections by class (count, denominator 8):

| Model | BOF | Command injection | SQL injection | XSS |
|---|---:|---:|---:|---:|
| Prompted baseline (no adapter) | 0 | 0 | 1 | 0 |
| A: QLoRA (rank 16, alpha 32) | 1 | 0 | 0 | 0 |
| B: QLoRA (rank 32, alpha 64) | 1 | 0 | 0 | 0 |

### Lenient successful and failed repairs

| Model | Successful case IDs | Failed case IDs |
|---|---|---|
| Prompted baseline (no adapter) | bof_01, bof_02, bof_03, bof_04, bof_05, bof_06, bof_07, bof_08, cmdi_01, cmdi_02, cmdi_03, cmdi_04, cmdi_05, cmdi_07, cmdi_08, sqli_01, sqli_02, sqli_03, sqli_04, sqli_05, sqli_06, sqli_08, xss_01, xss_02, xss_03, xss_04, xss_05, xss_06, xss_07, xss_08 | cmdi_06, sqli_07 |
| A: QLoRA (rank 16, alpha 32) | bof_01, bof_02, bof_03, bof_05, bof_06, bof_07, bof_08, cmdi_01, cmdi_02, cmdi_04, cmdi_06, cmdi_07, cmdi_08, sqli_01, sqli_02, sqli_03, sqli_04, sqli_05, sqli_06, sqli_07, sqli_08, xss_01, xss_02, xss_03, xss_04, xss_05, xss_06, xss_07, xss_08 | bof_04, cmdi_03, cmdi_05 |
| B: QLoRA (rank 32, alpha 64) | bof_01, bof_02, bof_03, bof_05, bof_06, bof_07, cmdi_01, cmdi_02, cmdi_03, cmdi_06, cmdi_07, cmdi_08, sqli_01, sqli_02, sqli_03, sqli_04, sqli_05, sqli_06, sqli_07, sqli_08, xss_01, xss_02, xss_03, xss_04, xss_05, xss_06, xss_07, xss_08 | bof_04, bof_08, cmdi_04, cmdi_05 |

## Failure analysis

### Format compliance

- Strict baseline rejects 9 responses: eight command-injection outputs put `import subprocess` at module level, outside the only target function (for example `cmdi_01`), violating p5-v1; `sqli_07` puts `EXPLANATION:` before the closing fence. Lenient tests the sensitivity to relocating those imports.
- A and B each reject `bof_04`: A lists `INCLUDES: <stdio.h>, <unistd.h>`; B lists `INCLUDES: <stdio.h>, <stdlib.h>, <unistd.h>`. `<unistd.h>` is not approved; lenient keeps rejecting it.
- Lenient baseline rejects only malformed `sqli_07`; lenient A and B still reject only `bof_04`. No response accepted in strict was rejected in lenient.

### Functional, attack, and scanner failures

- A `cmdi_03`: `backup_folder` returns `shutil.make_archive(...)`; P1 functional assertion expects status `0`. A `cmdi_05`: `show_file` returns bytes, while the case expects subprocess-style return code and stdout. Both formats are accepted, but the functional test fails.
- B `bof_08`: code clamps `len` only when `len > sizeof(buf)`, then writes `buf[len] = '\0'`; at equality this writes one byte out of bounds. AddressSanitizer reports stack-buffer-overflow in the attack test, and scanner findings persist.
- Lenient baseline `cmdi_06` claims `os.system(f"rm -f {filename}")` is safe and leaves it unchanged. The attack test observes `pwned`, and the scanner still finds shell execution.
- Scanner clearance is separate from Fix Rate. Strict scanner-uncleared cases: baseline BOF `bof_05`–`bof_08`; A `bof_07`, `bof_08`; B `bof_07`, `bof_08`. Where the other three Fix conditions pass, those cases remain Fix successes but not scanner clearances.
- Strict baseline CMDi cases are format rejections, so generated-code checks do not run. They count against denominators; this is format non-compliance, not evidence all eight patches failed functional or attack checks. Lenient mode executes them through the same Docker checks.

## Limitations

- 32 DEV cases (8 per class); class rates move in 12.5 percentage-point steps. No statistical-significance claims.
- Supervisor accepted no Kaggle rerun. The runner actually used differs from the repo runner; SHA-256 `0fd47ed6030ec12002d728fc422ef12f2777e81628234fd60918031d21a75596`. It used `device_map=auto` in the Kaggle T4 × 2 environment; actual GPU placement is not recorded.
- Legacy rows have `base_revision_status`, `gpu_devices_used`, `model_dtype`, `training_settings_provenance`, generated token counts, and finish reasons **NOT RECORDED**. Truncation cannot be measured.
- Base revision `c03e6d358207e414f1eca0bb1891e29f1db0e242` is an approximation. Run1 records the same NF4 inference settings, but identical NF4 training settings are assumed, not proven by the legacy output.
- A is rank 16/alpha 32; B rank 32/alpha 64; rank and alpha differ together.
- Greedy plus fixed seed is not a guarantee of bitwise GPU determinism; no determinism test was used for these metrics.
- `corpus/dev/` contains no gold `repair.c`; evaluated behavior comes from P1 assertions/tests rather than gold repair diffs.
- Function-to-diff conversion extends P1 raw-diff evaluation. Strict is the decision mode; lenient is secondary and reverses the DEV recommendation.
- Sealed benchmark/test data were not accessed; DEV results do not establish sealed performance.

## Self-audit

| Acceptance criterion | Status | Evidence |
|---|---|---|
| Same 32 dev cases (32 IDs × 3 conditions) | PASS | Both selected run directories contain 96 unique model/case rows covering the same 32 DEV IDs. |
| Same prompt version and temperature/generation | PASS | p5-v1, temperature 0, seed 42, max 2048, context 8192; matching prompt/tokenized-input hashes per case. |
| P1 methodology | PASS | Five P1 formulas unchanged and recomputed from per-case records; function-to-diff extension disclosed. |
| Overall and per-class results | PASS | OVERALL plus four classes per model; denominators 32 overall, 8 per class. |
| Reproducible | PASS WITH LIMITATIONS | Raw JSONL/manifest, SHA hashes, v3 freeze, image ID, versions, commands, per-case records and evidence retained; legacy Kaggle runtime details remain missing. |
| Recommendation based on measured results | PASS | Strict Fix: baseline 23/32, A 29/32, B 28/32. Lenient sensitivity is separate and reverses the decision. |
| Strict behavior unchanged | PASS | Current strict replay matched old strict run per case on raw format, failures, exact diff, and all five metric booleans (zero mismatches). |
| Lenient does not reject a strict-accepted response | PASS | Per-response comparison: zero such cases. |
| No benchmark/test access | PASS | DEV-only replay manifests and exact DEV matrix. |
| Full test suite | PASS | `151 passed, 5 skipped, 101 subtests passed`; one upstream Starlette/httpx deprecation warning. |

Independent audit recomputed every model/class/metric numerator and denominator from the selected `records.jsonl`, and matched all values in each `summary.json`: zero mismatches. Strict run has 96 rows and zero infrastructure errors; lenient run has 96 rows and zero infrastructure errors.

**Final verdict: DONE.** Strict DEV results recommend both adapters over the prompted baseline; A is the highest observed strict Fix Rate. Lenient sensitivity would recommend neither over baseline. Use strict mode for the decision as specified, and evaluate the sealed benchmark independently.
