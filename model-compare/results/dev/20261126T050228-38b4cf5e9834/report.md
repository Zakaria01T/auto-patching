# DEV repair evaluation (STRICT format mode)

Format mode: **strict**. This report aggregates only this mode; strict and lenient records cannot be combined.

Legacy input provenance: `base_revision_status`, `gpu_devices_used`, `model_dtype`, `training_settings_provenance`, `generated_token_count`, and `finish_reason` are **NOT RECORDED**. `device_map` is `auto` per the runner source, but actual device placement is not recorded. See `manifest.json` and per-case `inference_provenance`.

Legacy manifest input: **true**.

Percentages are suppressed when infrastructure is incomplete. Counts retain all assigned cases.

| Model | Class | Total | Valid % | Functional % | Attack % | Scanner % | Fix % |
|---|---|---|---|---|---|---|---|
| fine-tuned:hf-qwen7b-nf4-qlora | sql_injection | 8 | 100.00 (8/8) | 100.00 (8/8) | 100.00 (8/8) | 100.00 (8/8) | 100.00 (8/8) |
| fine-tuned:hf-qwen7b-nf4-qlora | xss | 8 | 100.00 (8/8) | 100.00 (8/8) | 100.00 (8/8) | 100.00 (8/8) | 100.00 (8/8) |
| fine-tuned:hf-qwen7b-nf4-qlora | command_injection | 8 | 100.00 (8/8) | 75.00 (6/8) | 100.00 (8/8) | 100.00 (8/8) | 75.00 (6/8) |
| fine-tuned:hf-qwen7b-nf4-qlora | buffer_overflow | 8 | 87.50 (7/8) | 87.50 (7/8) | 87.50 (7/8) | 62.50 (5/8) | 87.50 (7/8) |
| fine-tuned:hf-qwen7b-nf4-qlora | OVERALL | 32 | 96.88 (31/32) | 90.62 (29/32) | 96.88 (31/32) | 90.62 (29/32) | 90.62 (29/32) |
| fine-tuned:hf-qwen7b-nf4-rank32 | sql_injection | 8 | 100.00 (8/8) | 100.00 (8/8) | 100.00 (8/8) | 100.00 (8/8) | 100.00 (8/8) |
| fine-tuned:hf-qwen7b-nf4-rank32 | xss | 8 | 100.00 (8/8) | 100.00 (8/8) | 100.00 (8/8) | 100.00 (8/8) | 100.00 (8/8) |
| fine-tuned:hf-qwen7b-nf4-rank32 | command_injection | 8 | 100.00 (8/8) | 75.00 (6/8) | 100.00 (8/8) | 100.00 (8/8) | 75.00 (6/8) |
| fine-tuned:hf-qwen7b-nf4-rank32 | buffer_overflow | 8 | 87.50 (7/8) | 87.50 (7/8) | 75.00 (6/8) | 62.50 (5/8) | 75.00 (6/8) |
| fine-tuned:hf-qwen7b-nf4-rank32 | OVERALL | 32 | 96.88 (31/32) | 90.62 (29/32) | 93.75 (30/32) | 90.62 (29/32) | 87.50 (28/32) |
| prompted:hf-qwen7b-nf4-base | sql_injection | 8 | 87.50 (7/8) | 87.50 (7/8) | 87.50 (7/8) | 87.50 (7/8) | 87.50 (7/8) |
| prompted:hf-qwen7b-nf4-base | xss | 8 | 100.00 (8/8) | 100.00 (8/8) | 100.00 (8/8) | 100.00 (8/8) | 100.00 (8/8) |
| prompted:hf-qwen7b-nf4-base | command_injection | 8 | 0.00 (0/8) | 0.00 (0/8) | 0.00 (0/8) | 0.00 (0/8) | 0.00 (0/8) |
| prompted:hf-qwen7b-nf4-base | buffer_overflow | 8 | 100.00 (8/8) | 100.00 (8/8) | 100.00 (8/8) | 50.00 (4/8) | 100.00 (8/8) |
| prompted:hf-qwen7b-nf4-base | OVERALL | 32 | 71.88 (23/32) | 71.88 (23/32) | 71.88 (23/32) | 59.38 (19/32) | 71.88 (23/32) |

Failure reasons (multiple per case):

{
  "scanner_finding_persisted": 8,
  "response must contain exactly the target function": 8,
  "invalid_response_format": 1,
  "INCLUDES contains a non-approved standard header": 2,
  "functional_test_failed": 4,
  "sanitizer_error": 1
}

See manifest.json for frozen conditions and records.jsonl for skipped checks, durations and evidence.

Raw function-response format compliance (separate from the five P1 metrics):

| Model | Valid raw format | Assigned |
|---|---:|---:|
| fine-tuned:hf-qwen7b-nf4-qlora | 31/32 (96.88%) | 32 |
| fine-tuned:hf-qwen7b-nf4-rank32 | 31/32 (96.88%) | 32 |
| prompted:hf-qwen7b-nf4-base | 23/32 (71.88%) | 32 |

P1 metrics are computed after the strict p5-v1 function-to-diff adapter. P1 originally judged raw unified diffs; see the evaluation methodology for this documented extension.
