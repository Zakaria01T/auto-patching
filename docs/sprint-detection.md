# Sprint 2 — detection, then patch generation

`main` can upload a file and detect Python or C. It cannot show findings or a recall number. This sprint stops at scanning, plus one check that the pinned model answers. The repair prompt, the diff, and patching are sprint 3. Docker and pull requests stay out.

Do not redo what is already on `main`: `POST /jobs`, `GET /jobs/{id}`, the Streamlit upload, `docs/scanners.md`, `corpus/dev/_template/`, `configs/model.yaml` (`qwen2.5-coder:3b`), and `docs/training.md`.

Seven seats, one task each. Detection is the first half of every task that has both. A model call before a finding exists is not the demo.

## How to work together

Make five Trello lists, one per wave. A person only pulls a card from the next list when this wave’s “wave ends when” line is true. Inside one list, the cards run at the same time.

P1 is alone in wave 1. P6 may also merge the GPU commit during wave 1, because that commit already exists and does not depend on the finding file.

## Wave 1 — the contract

One hour. P1 commits. Everyone else reads that commit, then starts wave 2. No model call.

### P1 — Write the finding contract

What to do.

- Add `docs/findings.md`. A finding has `file`, `line`, `cwe`, `severity` (`high`, `medium`, or `low`), `rule_id`, `language`, `owasp`. Same file, line, and CWE from two tools is one finding.
- Classes: `sql_injection` CWE-89, `xss` CWE-79, `command_injection` CWE-78, `buffer_overflow` CWE-120. The first three use OWASP `A03:2021-Injection`. Buffer overflow uses `owasp: null`.
- Update `docs/job.md`. This sprint may fill `findings`. `diff`, `explanation`, `attempts`, and `decision` stay `null`.
- Status names stay the ones in `api/main.py`. A finished scan is `clean` when the list is empty. A finished scan with findings stays `scanning` and holds the list. Do not set `patching`. Do not add a status.

Done when. `docs/findings.md` is on `main`.

You hand to the other six. They use this file. They do not invent a second shape.

### P6 — Merge the GPU sentence

What to do. Merge `2ec089a` from `origin/p6/sprint2-gpu-decision`. Do not write a second GPU story.

Done when. The README points at `docs/training.md`.

Wave 1 ends when both of those commits are on `main`.

## Wave 2 — six people, no waiting on each other

Starts the moment wave 1 is on `main`. These cards are parallel. P5 may ping the model. P5 does not send a finding or ask for a diff. P2 does not call the model. P6 does not train.

### P4 — First cases

What to do. Two cases per class in the shape of `corpus/dev/_template/`: `sql_injection`, `xss`, `command_injection`, `buffer_overflow`. One small function each. `meta.json` holds id, language, class, and CWE from `docs/findings.md`. `test.txt` states a normal input and the normal result. Leave the reviewer seat blank.

Done when. Eight folders exist, two per class, and you post the paths for P3.

You hand the paths to P3, P5, and P6.

### P3 — Scan a safe file

What to do. Add `scanner.scan(path, language)`. Semgrep and Bandit for Python. Flawfinder and cppcheck for C. Use `docs/scanners.md`. Map each tool onto the fields in `docs/findings.md`. `docs/samples/sample.py` returns `[]`. Commit any Semgrep rule in the repo.

Done when. A Python shell call on the safe file returns an empty list, and P2 can import `scan`.

You hand the function to P2.

### P5 — Four rules, no model

What to do. Four files, six to ten lines each, under `patcher/rules/`. One class each. The repairs are a parameterized query, encoding on the way into the page, a fixed argument list with no shell string, and a bounded copy plus a length check. Do not call Ollama.

Done when. The four files are on `main`.

You hand the rule paths to sprint 3. Nobody in this sprint is blocked on them.

### P5 — Reach the model, do not ask it to patch

What to do. Call the tag in `configs/model.yaml` with a one-line check, for example a request to reply with the single word `ready`. Log the tag and that reply in `docs/model.md`. Do not send a finding, a source file, a CWE, or a request for a diff. The job API does not call Ollama.

Done when. A teammate can see the tag and the reply in `docs/model.md`.

You hand nothing to P2. Sprint 3 is what connects the model to a finding.

### P6 — Empty training-row file

What to do. Add the JSONL field names `finding`, `vulnerable code`, and `repair`. The row count is zero. No benchmark ids. Do not train.

Done when. The empty row file is on `main`.

### P2 — Safe file ends clean

What to do. Keep `POST /jobs` on `uploaded`. A background task calls `scanner.scan`. An empty list sets `clean` and `findings` to `[]`. Do not call the model. Update `tests/test_jobs.py` so a safe `.py` file ends `clean` and a `.txt` file stays `rejected`.

Done when. A second person fetches a `clean` job for `docs/samples/sample.py`.

You hand that GET response to P7.

### P7 — Page shows clean

What to do. Poll `GET /jobs/{id}` until status is `clean`. Show clean. Disable the repository URL box. Do not fetch an address. No scanner import and no Ollama call in `ui/`.

Done when. Another machine uploads the safe sample and the page says clean.

Wave 2 ends when the safe file is `clean` on the page, eight first cases are on `main`, and the four rule files exist.

## Wave 3 — findings on a real case

Starts when wave 2 has ended. Still no Ollama call. Talk in one channel: P4 posts each new path, P3 says if it produced a finding, P5 or P6 says if they accept the review.

### P4 — Eight cases per class

What to do. Grow each class to eight. Same template. Put P5’s seat on `sql_injection` and `xss` only after P5 has reviewed them. Put P6’s seat on `command_injection` and `buffer_overflow` only after P6 has reviewed them. `benchmark/` stays empty.

Done when. A count check fails if any class has fewer than eight, and every case names a reviewer who is not you.

You keep handing new paths to P3.

### P3 — One Python finding and one C finding

What to do. Point `scan` at one `sql_injection` case and one `buffer_overflow` case. Drop findings that share file, line, and CWE. Do not write a rule that matches only a variable name from the first file.

Done when. The Python case returns `CWE-89` and the C case returns `CWE-120`. The safe file still returns `[]`.

You hand `scan` to P2 again, this time with real findings.

### P5 — Review SQL injection and XSS

What to do. Read the source and the normal test. Reject a case that is one big application. Your seat goes in `meta.json` only when you accept it.

Done when. Every `sql_injection` and `xss` case names you, or you have sent it back to P4.

### P6 — Review command injection and buffer overflow

What to do. Same review rule as P5, for `command_injection` and `buffer_overflow`.

Done when. Every case in those two classes names you, or you have sent it back to P4.

### P1 — Recall table

What to do. A case counts when a finding’s CWE matches its `meta.json`. Print class, cases, detected, and recall. Target is at least 90% overall. Name any class under 90% and open one missed file. Give that path to P3.

Done when. The table prints every class.

You hand a miss, if there is one, to P3.

### P2 — GET returns findings

What to do. When `scan` returns a non-empty list, store it on the job. Leave the model uncalled. `GET /jobs/{id}` returns those findings. Do not add a pull-request route.

Done when. A second person fetches the SQL job and sees `CWE-89` in `findings`.

You hand that JSON to P7.

### P7 — Page shows the finding

What to do. When `findings` is a non-empty list, show file, line, CWE, and severity. Keep the URL box disabled.

Done when. Another machine sees those four fields for the Python case and the C case.

Wave 3 ends when the page shows one Python finding and one C finding, and P1’s table has a number for every class.

## This sprint is done when

Trello already has waves 1 to 3. That is the sprint. Do not add waves 4 and 5 to this board.

At the review you can show all of this:

1. A safe file on the page says clean. The model was not called.
2. One Python case and one C case show file, line, CWE, and severity.
3. The recall table is at least 90% overall. Every class is printed. The weakest class is named and one miss is opened.
4. The URL box does not fetch a repository.
5. `docs/model.md` shows that `qwen2.5-coder:3b` answered a one-line check. No finding was sent, and no diff was requested.

The repair prompt is not required for this list. Do not add a Trello card that sends a case to the model.

## Sprint 3 — prompting

Not this sprint. Leave these cards off the current Trello board.

## Wave 4 — one diff per class

Starts when wave 3 has ended. P4, P5, and P6 work on train files. P2 and P7 wait until `generate` returns, then they connect it. SQL goes through the whole wave before the other classes.

### P4 — Gold repairs

What to do. Two repairs per class under `corpus/train/`, not under `corpus/dev/`. Parameterized query, encoded output, no shell string, bounded C copy. The normal test passes on the repaired file. Do not delete the function.

Done when. A second person applies each gold diff and the test passes. Post the SQL train path first.

You hand train paths to P5 and P6.

### P5 — Ollama

What to do. `patcher.generate` reads the finding from the job. The prompt is the finding, a request for a unified diff then a short explanation, the CWE, the OWASP category, the rule file, the snippet, the functional test, and one example from `corpus/train/` only. Same function names, no deleted feature, no extra files. Call `qwen2.5-coder:3b` with the temperature in `configs/model.yaml`. Log the tag, a prompt version, and the raw answer. If it is not a diff, record a failed format. Do not hand-edit it into a success. Start with SQL.

Done when. The review runs the command and the log header shows `qwen2.5-coder:3b`.

You hand `generate` to P2.

### P6 — Rows from the gold diffs

What to do. Fill the JSONL file from `corpus/train/` only. Print the count. Zero benchmark ids. Do not train until the count is greater than zero. If you then train, record base model, rank, and steps, and leave the adapter unloaded. If the notebook fails, write the error and stop. The product stays on `qwen2.5-coder:3b`.

Done when. The row count is in the repo and the default model is still the prompted one.

### P2 — Store the diff

What to do. On a non-empty finding list, set `patching` and call `patcher.generate`. Store `diff`, `explanation`, and `attempts`. Save the raw answer under `data/uploads/<id>/`. An empty list stays `clean` and never calls the model. Change the README line that says the last five fields are always `null`.

Done when. A second person fetches a job whose `diff` and `explanation` are filled.

You hand that job id to P7.

### P7 — Page shows the diff

What to do. Show `diff` and `explanation` with the words “not validated.” No pull-request button.

Done when. Another machine sees a diff marked not validated.

Wave 4 ends when SQL has a diff on the page, and each other class either has one too or is named as failed.

## Wave 5 — the two checks that close the sprint

Starts when wave 4 has a diff for SQL and the dev set has eight cases per class. P3 and P1 work at the same time. Everyone else fixes only what these two send back.

### P3 — Recall stays at 90%

What to do. Re-run P1’s recall command on all eight cases per class. Fix a rule that misses a class or that flags a gold repair. Do not read `benchmark/`.

Done when. The command still prints at least 90%, and one Python file, one C file, and one safe file behave as in wave 3.

### P1 — Smoke table

What to do. About eight dev cases, all four classes. Columns: diff produced, applies by hand, functional test passes. One success per class. A gold diff pasted over the model output does not count. Name the class that failed.

Done when. The table is in the sprint notes and one success is shown live per class, or the failed class is named.

Wave 5 ends when both of those are true. That is the end of the sprint. Docker and pull requests are not in it.

## Shared rules

A finding has exactly these fields:

```json
{
  "file": "app.py",
  "line": 42,
  "cwe": "CWE-89",
  "severity": "high",
  "rule_id": "python.lang.security.audit.sqli",
  "language": "python",
  "owasp": "A03:2021-Injection"
}
```

`severity` is `high`, `medium`, or `low`. Same file, same line, same CWE from two tools is one finding.

| Class | CWE | Language | OWASP |
| --- | --- | --- | --- |
| sql_injection | CWE-89 | python | A03:2021-Injection |
| xss | CWE-79 | python | A03:2021-Injection |
| command_injection | CWE-78 | python | A03:2021-Injection |
| buffer_overflow | CWE-120 | c | `null` |

Status names stay the ones in `api/main.py`. `clean` means the finding list is empty and the model was not called. `patching` means a finding exists and the model was asked. `decision` stays `null`. Do not set `validating`, `accepted`, or `needs_human`.

P5 reviews `sql_injection` and `xss`. P6 reviews `command_injection` and `buffer_overflow`. The author of a case is not its reviewer.

## P1 — Recall report, then the smoke table

Why. The detection goal is a number per class. The patch goal is one real diff per class, not a percentage for the jury.

What to do.

- On day 1, add `docs/findings.md` with the object and the status rules above. Update `docs/job.md` so this sprint may fill `findings`, `diff`, `explanation`, and `attempts`.
- A case is detected when a finding’s CWE matches that case. Print class, cases, detected, and recall. The target is at least 90% overall. Name any class under 90% and open one missed file.
- After generate works, score about eight dev cases, all four classes. Columns: diff produced, applies by hand, functional test passes. The sprint needs one success per class.
- A gold diff pasted over the model output does not count.

Done when. The review shows the recall table, with the weakest class named and one miss opened, and the smoke table, with one live success per class or the failed class named.

Common miss. One average that hides a class at 40%.

## P2 — Store findings, then the diff

Why. The upload API stops at `uploaded`. The page cannot show a finding or a diff until this job holds them.

What to do.

- Keep `POST /jobs` on `uploaded`. In a background task, call `scanner.scan`. An empty list sets `clean` and `findings` to `[]`. Do not call the model.
- A non-empty list stores `findings`, sets `patching`, and calls `patcher.generate` for one finding at a time. Store `diff`, `explanation`, and `attempts`.
- Save the raw model answer under `data/uploads/<id>/`. That directory stays gitignored.
- Update `tests/test_jobs.py`. A safe file ends `clean`. A `.txt` file stays `rejected`. The assertion that `findings` is always `null` has to change.
- Change the README line that says the last five fields are always `null`.
- Do not add a pull-request route.

Done when. A second person fetches a `clean` job and a job whose `diff` and `explanation` are filled.

Common miss. Detecting the language with the model.

## P3 — Four tools, one finding list

Why. The diagram names Semgrep, Bandit, Flawfinder, and cppcheck. Shipping one of them and skipping the others will show up in the review.

What to do.

- `scanner.scan(path, language)` maps every tool onto file, line, CWE, severity, rule id, and language.
- Semgrep and Bandit for Python. Flawfinder and cppcheck for C. Commands are in `docs/scanners.md`.
- Drop duplicate findings that share file, line, and CWE.
- Commit the Semgrep rules you wrote. Do not leave them only in a cloud account.
- Re-run P1’s recall command after P4 adds cases. Fix a rule that misses a class or that flags a gold repair. Stay at or above 90% on dev. Do not read `benchmark/`.

Done when. One Python file and one C file each produce a finding, a safe file produces an empty list, and the recall command still prints at least 90%.

Common miss. A rule that matches only the variable name in your first sample. Recall will look perfect and will not survive the next file.

## P4 — Dev cases, then gold diffs

Why. Recall needs planted flaws with a known CWE. The model needs human repairs, and those repairs must not be the files you score.

What to do.

- At least eight cases per class: `sql_injection`, `xss`, `command_injection`, `buffer_overflow`. Two per class land on day 1 so P3 can scan. Use `corpus/dev/_template/`. Each case is one small function. `meta.json` holds id, language, class, CWE, and the reviewer’s seat.
- A functional test uses a normal input and checks the feature. Write it now. Sprint 4 needs it.
- Do not create the sealed benchmark. `benchmark/` stays empty.
- Then two gold repairs per class under `corpus/train/`: parameterized query, encoded output, no shell string, bounded C copy. The functional test passes on the repaired file. The few-shot loader refuses to read `benchmark/`.

Done when. A count check fails if a class drops under eight. Every dev case has a reviewer who is not the author. A second person applies each gold diff and the test passes.

Common miss. One large web application as a single case, or a gold repair that deletes the function.

## P5 — Rules first, then Ollama

Why. The four repair rules were not written. The model box is a local code model, not a website tab.

What to do.

- Four files, six to ten lines each, under `patcher/rules/`. One class each. No model call in these files.
- Then `patcher.generate` reads the finding JSON from the job and builds the prompt from the five parts: one finding, unified diff then a short explanation, the CWE and OWASP category and the rule, the snippet and the functional test, one train example, and the constraints (same function names, no deleted feature, no extra files).
- Call Ollama with `configs/model.yaml`. Temperature comes from that file. The tag is `qwen2.5-coder:3b`.
- Log the model tag, a prompt version, and the raw answer. If it is not a diff, record a failed format. Do not hand-edit it into a diff and count it.
- Few-shot examples come from `corpus/train/` only.
- Review every `sql_injection` and `xss` case.

Done when. The four rule files are on `main`, and the review runs the generate command. The log header shows the model tag.

Common miss. Pasting the file into a chat during the review, or a secret prototype that replaces the scanner demo.

## P6 — Review cases, then training rows

Why. The Kaggle check is already in `docs/training.md`. The unread part is the case review, the row format, and an optional adapter that must not become the product.

What to do.

- Merge `2ec089a` from `origin/p6/sprint2-gpu-decision` so the README states the GPU sentence. Do not write a second GPU story.
- Review every `command_injection` and `buffer_overflow` case.
- JSONL rows from the gold diffs: finding, vulnerable code, repair. Print the count. Zero benchmark ids.
- If the notebook works, train a small adapter and record base model, rank, and steps. If it does not, write the error and stop. The product keeps `qwen2.5-coder:3b` with no adapter loaded.
- CVEfixes or Juliet may be added only after you can name the license and exclude anything that might later sit in the benchmark.

Done when. The README points at `docs/training.md`, a config file and a row count are in the repo, and the default model is still the prompted one.

Common miss. Training on the same files you plan to score.

## P7 — Clean, findings, then the diff

Why. The page uploads a file and then says findings arrive later. The jury has to see the scan, and later the diff, without a fake pull request.

What to do.

- Poll `GET /jobs/{id}` after upload.
- A safe file shows clean.
- A case shows file, line, CWE, and severity.
- When `diff` is present, show the diff and the explanation with the words “not validated.”
- The repository URL control stays disabled. Do not fetch an address the user types.
- No pull-request button. No scanner import and no Ollama call in `ui/`.

Done when. A second person on another machine sees clean, then findings, then a diff marked not validated.

Common miss. A button that says “open pull request” and does nothing, or worse, opens one.

## Review for this sprint

1. Upload a safe file. The page says clean.
2. Upload one Python case and one C case. Show file, line, CWE, severity.
3. Show the recall table. Open one miss.
4. Show that a repository URL is not an open door to any host.
5. P5 shows the one-line model reply in `docs/model.md`. The page still has no diff.

Be ready to explain why a miss can never count as a fix, and why four tools feed one JSON. Sending a finding to the model is sprint 3, not this review.

## If you fall behind

Protect the upload, the four tools on at least one file each, and the recall table. If a class is stuck, spend the last days on that class. The one-line model check can slip. Do not start the repair prompt to make the sprint feel further along.
