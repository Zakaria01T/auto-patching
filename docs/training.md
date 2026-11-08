LoRA training will run on Kaggle using the free notebook with two Tesla T4 GPUs (15 GB each), which I opened and confirmed on 2026-10-20 (`nvidia-smi` showed both GPUs; the session panel showed a 12 hour session and 30 GiB of RAM). The training data will be pairs of vulnerable code and a repair. The model stays frozen and only a small adapter is trained, so the prompted model remains the default and LoRA is a comparison. Google Colab is the backup: a free Tesla T4 (about 15 GB) was also confirmed there on 2026-10-19, with a free runtime of up to about 5.5 hours.

## Training rows

Training rows go in [`training/rows.jsonl`](../training/rows.jsonl), one JSON object per line. The file is empty for now: the row count is 0. The eight gold rows are built in [`training/gold.jsonl`](../training/gold.jsonl) (see "Gold repairs" below) and are added to `rows.jsonl` when the team starts a run.

## Dataset schema (extended)

The three existing fields are unchanged: `finding`, `vulnerable_code`, `repair`. Four fields are added. No new schema is introduced.

| Field | Content |
| --- | --- |
| `finding` | The finding the scanner reported, with the seven fields `file`, `line`, `cwe`, `severity`, `rule_id`, `language`, `owasp` (see [findings.md](findings.md)). `owasp` is `null` for Flawfinder and cppcheck findings |
| `vulnerable_code` | The flawed code the finding points at |
| `repair` | The complete corrected function. C repairs include their headers; Python repairs keep their imports inside the function |
| `explanation` | One sentence describing the fix |
| `source` | Source type and path or link: `gold:corpus/train/<id>`, `sven:<link>` or `juliet:<path>` |
| `class` | One of `sql_injection`, `xss`, `command_injection`, `buffer_overflow`, as in [findings.md](findings.md) |
| `cwe` | CWE id as in [findings.md](findings.md), for example `CWE-89` |

An example row, shown here and not in the file:

```json
{"finding": {"file": "corpus/train/gold_sqli_01/vulnerable.py", "line": 2, "cwe": "CWE-89", "severity": "high", "rule_id": "scanner.rules.python-sql-string-concat", "language": "python", "owasp": "A03:2021-Injection"}, "vulnerable_code": "def find_invoice(conn, number):\n    query = \"SELECT id, total FROM invoices WHERE number = '\" + number + \"'\"\n    return conn.execute(query).fetchall()\n", "repair": "def find_invoice(conn, number):\n    query = \"SELECT id, total FROM invoices WHERE number = ?\"\n    return conn.execute(query, (number,)).fetchall()\n", "explanation": "Replaced string concatenation with a parameterized query so the invoice number is bound as data.", "source": "gold:corpus/train/gold_sqli_01", "class": "sql_injection", "cwe": "CWE-89"}
```

Rules:

- Rows come from `corpus/train/` only. Nothing from `corpus/dev/` or `benchmark/` is ever a training row, so the model is never trained on the cases it is scored on.
- The row count is printed with `wc -l training/rows.jsonl`.
- No training run happens until the count is greater than 0.

## Gold repairs

Eight manually reviewed repairs live in `corpus/train/`, never in `corpus/dev/`:

| Class | Cases |
| --- | --- |
| sql_injection | `gold_sqli_01`, `gold_sqli_02` |
| xss | `gold_xss_01`, `gold_xss_02` |
| command_injection | `gold_cmdi_01`, `gold_cmdi_02` |
| buffer_overflow | `gold_bof_01`, `gold_bof_02` |

Each folder holds `vulnerable.*`, `repair.*`, `meta.json`, `test.txt` (normal input and result) and `attack.txt` (attack input and when it counts as blocked).

Commands, run on Linux or in Docker (they need `tar`, `head`, `gcc` and the pinned scanners):

```bash
python training/validate_gold.py            # validate the 8 repairs
python training/build_rows.py               # build training/gold.jsonl
python training/build_rows.py --require-reviewer   # final build: stops if a reviewer is missing
```

### Validation

For each repair:

1. The normal test in `test.txt` passes.
2. The attack input in `attack.txt` is blocked. The attack was also run on the vulnerable version to confirm it works there.
3. Python repairs: the original finding (same rule ID as on the vulnerable file) is no longer reported.
4. C repairs: compiled with `gcc -std=c11 -fsanitize=address` and run with a 100-character input. There is no AddressSanitizer error. The scanner status is recorded separately because Flawfinder may still flag a correct fix.
5. A second person reviews the repair (see Review).

Results of the last run (8 of 8 pass):

| Repair | Original finding, gone after the repair | Other findings still reported (recorded only) |
| --- | --- | --- |
| gold_sqli_01 | scanner.rules.python-sql-string-concat | none |
| gold_sqli_02 | B608 | none |
| gold_xss_01 | scanner.rules.python-html-concat | none |
| gold_xss_02 | scanner.rules.python-html-fstring | none |
| gold_cmdi_01 | scanner.rules.python-command-shell | Bandit B404, B607 (informational) |
| gold_cmdi_02 | scanner.rules.python-command-shell | Bandit B404, B607 (informational) |
| gold_bof_01 | Flawfinder FF1005 | FF1010, FF1013, FF1022 |
| gold_bof_02 | Flawfinder FF1015 | FF1013 |

Notes:

- The two XSS repairs build the HTML with `str.format` after `html.escape`. The scanner's Semgrep HTML rules flag any f-string or concatenation that builds HTML, even when the value is escaped.
- `gold_xss_02` also accepts only `http` and `https` URLs, because HTML escaping alone does not stop a `javascript:` URL.

### Review

Each repair is reviewed by a second person (P5 or P6), recorded in the `reviewer` field of its `meta.json`. `gold.jsonl` is rebuilt with `--require-reviewer` after the review.