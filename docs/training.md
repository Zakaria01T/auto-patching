LoRA training will run on Kaggle using the free notebook with two Tesla T4 GPUs (15 GB each), which I opened and confirmed on 2026-10-20 (`nvidia-smi` showed both GPUs; the session panel showed a 12 hour session and 30 GiB of RAM). The training data will be pairs of vulnerable code and a repair. The model stays frozen and only a small adapter is trained, so the prompted model remains the default and LoRA is a comparison. Google Colab is the backup: a free Tesla T4 (about 15 GB) was also confirmed there on 2026-10-19, with a free runtime of up to about 5.5 hours.

## Training rows

Training rows go in [`training/rows.jsonl`](../training/rows.jsonl), one JSON object per line. The file is empty for now: the row count is 0. Rows are added from the gold repairs in `corpus/train/` once they exist.

Each row has three fields:

| Field | Content |
| --- | --- |
| `finding` | The finding the scanner reported, with the seven fields `file`, `line`, `cwe`, `severity`, `rule_id`, `language`, `owasp` (see "Shared rules" in [sprint-detection.md](sprint-detection.md)) |
| `vulnerable_code` | The flawed code the finding points at |
| `repair` | The same code after the human repair |

An example row, shown here and not in the file:

```json
{"finding": {"file": "app.py", "line": 42, "cwe": "CWE-89", "severity": "high", "rule_id": "python.lang.security.audit.sqli", "language": "python", "owasp": "A03:2021-Injection"}, "vulnerable_code": "cur.execute(\"SELECT * FROM users WHERE name = '\" + name + \"'\")", "repair": "cur.execute(\"SELECT * FROM users WHERE name = ?\", (name,))"}
```

Rules:

- Rows come from `corpus/train/` only. Nothing from `corpus/dev/` or `benchmark/` is ever a training row, so the model is never trained on the cases it is scored on.
- The row count is printed with `wc -l training/rows.jsonl`.
- No training run happens until the count is greater than 0.
