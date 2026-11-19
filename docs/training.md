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
## C buffer overflow rows

[`training/c_rows.jsonl`](../training/c_rows.jsonl) holds 74 `buffer_overflow` rows in the schema above: 39 built from Juliet C/C++ 1.3 and 35 written for this project. The cases live in `corpus/train/juliet_*` and `corpus/train/own_bof_*` (`vulnerable.c`, `repair.c`, `meta.json`). They do not start with `gold_`, so `training/build_rows.py` is unchanged.

### Sources

- **Juliet (39 rows).** Baseline cases (flow variant 01) of `CWE121_Stack_Based_Buffer_Overflow` and `CWE122_Heap_Based_Buffer_Overflow` (see [sources.md](sources.md)). Only the vulnerable `bad()` function is used. Juliet's own good versions fix the input or the buffer size (176 of the 184 baseline cases use `goodG2B`) and leave the copy unchanged, so the repair that bounds the copy is written by `juliet_extract.py`. Comments that name the flaw, `dataBadBuffer` and the unused `dataGoodBuffer` are removed; Juliet helpers become plain C.
- **Own cases (35 rows).** Small functions that take input, like the dev and gold cases: `strcpy`, `strcat`, `sprintf`, `memcpy`, `strncpy` and `strncat` with a wrong bound, `sscanf` without a width, into stack arrays, struct fields and heap buffers. The names and patterns of `corpus/dev/bof_*` and the gold repairs are avoided. They were written with an AI assistant and checked as below.

Every row is labelled `buffer_overflow` / `CWE-120`, the class and CWE of [findings.md](findings.md). The original Juliet CWE stays in `source`.

### Validation

`check.py` runs in Docker with the network off. A pair is kept only if:

1. the team scanner reports CWE-120 on a line the repair changes (that finding is the row's `finding`);
2. both versions compile with `gcc -std=c11 -fsanitize=address`;
3. the vulnerable version stops with an AddressSanitizer error on the attack (a 200-character input; Juliet cases have the long data built in) and the repair exits 0 without one;
4. own cases: a normal input gives the same output on both versions.

The scanner result on the repair is recorded only: it still reports CWE-120 on 20 of the 35 own repairs and all 39 Juliet repairs (any `strncpy`, `memcpy` or fixed-size array).

`export.py` then compares each vulnerable function (comments, includes and whitespace removed) with `corpus/dev/`, the gold repairs and `benchmark/`, and drops exact matches and pairs with a similarity of 0.85 or more. None matched; the closest is `own_bof_13` against `corpus/dev/bof_08` (0.76). `benchmark/` is empty today, so the check has to run again before it is sealed.

### Counts

| Step | Juliet | Own |
| --- | --- | --- |
| Start | 184 baseline `.c` files | 36 cases |
| Family filter | 75 (dropped: 48 `wchar_t`, 30 off-by-one, 12 index checks, 8 struct field overruns, 6 allocation sizes, 3 `sizeof` of a pointer, 2 multibyte lengths) | 36 |
| Scanner reports CWE-120 on the copy | 39 (dropped: 15 copy loops, 15 `memmove`, 6 `snprintf`) | 35 (dropped: `vsprintf`, reported as CWE-134) |
| AddressSanitizer and normal behaviour | 39 | 35 |
| Deduplication | **39** | **35** |

Per-pair results are in `training/c_dataset/check.json`, `juliet_extract.json` and `dedupe.json`.

### Rebuild

Juliet is not in the repository (153 MB). Download it from the SARD page in [sources.md](sources.md) and unzip it outside the repository, then from the repository root:

```bash
python3 training/c_dataset/juliet_extract.py <unzipped>/C/testcases
python3 training/c_dataset/own_cases.py
docker run --rm --network none -v "$PWD":/repo:ro -v "$PWD/training/c_dataset":/work autopatch-casecheck python /work/check.py
python3 training/c_dataset/export.py
```

`autopatch-casecheck` is `python:3.12-slim` with gcc, cppcheck and `requirements-scanners.txt`.

## Python rows

[`training/python_rows.jsonl`](../training/python_rows.jsonl) holds 247 Python rows in the schema above: 95 `sql_injection`, 80 `command_injection`, 72 `xss`. The cases live in `corpus/train/python_*` (`vulnerable.py`, `repair.py`, `meta.json`).

### Sources

| Source | SQL injection | Command injection | XSS | Total |
| --- | --- | --- | --- | --- |
| `sven:` (SVEN, real commits) | 90 | 0 | 0 | 90 |
| `synthetic:` (ChatGPT, PR #22) | 5 | 43 | 13 | 61 |
| `cybernative:` (LLM, CyberNative DPO) | 0 | 1 | 0 | 1 |
| `generated:` (DeepSeek v4.1 Flash) | 0 | 36 | 40 | 76 |
| `generated:` (Nemotron 3 Ultra) | 0 | 0 | 19 | 19 |
| Total | 95 | 80 | 72 | 247 |

157 of 247 rows are LLM-generated. All the command injection and XSS rows are LLM-generated.

### Cleaning (`clean.py`)

The input is the 201 rows of PR #22 after its own cleaning (commit `2cc6bca`: flagged repairs and near duplicates removed, one-sentence explanations). They were re-scanned with `scanner/scan.py`. Most of them named rules that are not in `scanner/rules` (`python-sql-execute-dynamic`, `python-sql-percent-or-format`, `python-command-popen-getoutput`, `python-xss-mark-safe`, `python-xss-html-percent-or-format`, `python-xss-autoescape-off`), so each `finding` is now the repo scanner's own: the row's CWE, a rule the repair no longer reports, preferably on a changed line. The first version of the rows (commit `1c2a952`) had long explanations that often named a defect in the repair; that text is used for the defect check. A row was dropped when:

| Reason | Rows |
| --- | --- |
| The first explanation names a defect in the repair (bare scalar instead of a tuple, quotes left around the placeholder, ...) | 31 |
| No finding of the row's CWE on the vulnerable version | 9 |
| Quoted SQL placeholder (`'%s'`, `'{name}'`) | 2 |
| The explanation says the repair is broken or describes the bug instead of the fix (`sqli_0017`, `sqli_0038`, `sqli_0073`) | 3 |
| Placeholder function: unused parameter, undefined names (`xss_0014`, `xss_0016`) | 2 |
| Template injection labelled XSS: user input becomes the Jinja template source (`xss_0040`) | 1 |
| XSS repair puts the value at the start of an `href` without an `http`/`https` check (`xss_0011`) | 1 |

The same checks also drop repairs the scanner still flags, command injection repairs that keep a shell or leave a user value where it can be read as an option, hedged explanations and near duplicates (0.85); none of the 201 rows hit them. 201 rows → 152.

The last four reasons (`common.semantic_problem`) were added after the review of PR #23, which found those seven rows. They also check the code itself: a placeholder used as a table name (`insert into ? values`) and `?` with psycopg2 or MySQL are dropped even when the explanation says nothing. The same checks run on the generated candidates; none of the 100 hit them. Per-case decisions: `training/python_dataset/clean.json`.

### Generated rows (`validate.py`)

Candidates were written by free models through OpenCode, in a container with no access to the repository, from the prompts in `training/python_dataset/prompts/`; the raw output is in `candidates/`. A candidate becomes a row only if both versions are one function of at most 30 lines and parse; the explanation is one sentence of at most 30 words without hedges; the scanner reports the class's CWE on the vulnerable version and no longer reports that rule on the repair; command injection repairs keep no shell and pass no user value where it can be read as an option (it must follow `--` or an option flag, or the function rejects a leading `-` or checks an allow-list); XSS repairs escape (and check the scheme of a URL value); the checks of `common.semantic_problem` pass; and the vulnerable function is less than 0.85 similar to `corpus/dev/`, the gold cases, `benchmark/` and every other row. 100 candidates → 95 rows (3 argument injection, 1 near duplicate, 1 repair that does not escape). Per-candidate decisions: `validate.json`.

A random sample of 20 generated rows was read by a second model (Claude Sonnet) for what the scanner cannot check (correct fix, same behaviour on normal input, realistic code): 17 OK, 2 minor (one strict size check, one contrived request source), 1 argument injection, which led to the option check above.

### Limits

- Scanner false positives: the HTML rules flag any concatenation or f-string that builds HTML, even after `html.escape`, so the XSS repairs build HTML with `str.format` or `format_html`.
- The repo scanner does not flag `str.format` or `%` HTML, `bash -c` with an argument list, or `subprocess.getoutput`. A few rows therefore carry a weak finding, such as Bandit B404 (`import subprocess`) on `python_cmdi_0059`.
- The LLM-generated rows are not yet reviewed by a person (`reviewer` is `null`).

### Rebuild

```bash
training/python_dataset/build.sh
```

It restores the PR #22 rows (commit `2cc6bca`), runs `clean.py`, then `validate.py` on the candidates, in the `autopatch-casecheck` image with the network off. The model runs are not repeated: the candidates are kept in the repository.
