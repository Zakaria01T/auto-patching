# Background Scan (Stage 2 hookup)

Branch: `p2/background-scan`
Owner: P2 (API)

## Summary

After a file is uploaded to `POST /jobs`, the API now runs the scanner in a
FastAPI background task. The upload still answers immediately with
`status: "uploaded"`, and the scan result is stored on the job so it can be
fetched later with `GET /jobs/{id}`.

## How it works

1. `POST /jobs` receives the file, validates it, saves it, and writes the job record (`meta.json`).
2. The response returns right away with `"status": "uploaded"`.
3. If the file was accepted, `background_tasks.add_task(run_scan, job_id)` starts the scan.
4. `run_scan` calls `scanner.scan` on the saved file.
5. The result updates the job record:

| Scan result | Job status | `findings` |
|---|---|---|
| Empty (nothing found) | `clean` | `[]` |
| Non-empty | stays `scanning` (per `docs/sprint-detection.md`) | list of findings |
| Scan crashes | stays `scanning` | unchanged, private `error` field set |

Rules:

- Rejected files (wrong extension such as `.txt`, or too large) are **never scanned**.
- A clean result does **not** call any model.
- The job record is written through a temp file, then replaced, so the page never reads a half-written `meta.json`.
- A crash in the scan is logged with `logger.exception` and does not break the API.

## Files changed

| File | Change |
|---|---|
| `api/main.py` | `create_job` takes `background_tasks: BackgroundTasks`; added `run_scan`; atomic `write_meta` |
| `tests/test_jobs.py` | New tests: clean file, rejected file not scanned, findings stored, scan crash |
| `README.md` | `findings` is `[]` after a clean scan and holds the list when something is found. The other four fields stay `null` this sprint. |

`scanner/scan.py` is owned by P3 and is **not** part of this PR.

## Running the tests

```powershell
python -m pytest -v
```

Expected: **15 passed**. The API tests use a fake `scan`, so CI does not need
scanner tools. `test_safe_python_sample_is_empty` (P3) runs the real scanners
when they are available.

## Real check with the server

```powershell
cd C:\Users\hp\Desktop\5annee\DL\auto-patching
.venv\Scripts\Activate.ps1
python -m uvicorn api.main:app --reload
```

In a second terminal:

```powershell
# Safe file: expect "uploaded", then "clean" with "findings": []
curl.exe -F "file=@docs/samples/sample.py" http://localhost:8000/jobs
curl.exe http://localhost:8000/jobs/<id>

# Vulnerable file: expect "scanning" with a CWE-89 finding
curl.exe -F "file=@corpus/dev/sqli_01/source.py" http://localhost:8000/jobs
curl.exe http://localhost:8000/jobs/<id>
```

If the vulnerable file ends up `clean`, do not push. Tell P3 first: a
vulnerable file reported as clean is the worst failure for this tool.

For a real scan, install `requirements-scanners.txt` into `.venv-scanners`.
