### Check the scan results

Upload these three files, wait a few seconds, then fetch each job:

```
curl.exe -F "file=@corpus/dev/sqli_01/source.py" http://localhost:8000/jobs
curl.exe -F "file=@corpus/dev/bof_01/source.c" http://localhost:8000/jobs
curl.exe -F "file=@docs/samples/sample.py" http://localhost:8000/jobs
curl.exe http://localhost:8000/jobs/<id>
```

Job ids exist only on the machine that ran the API, so run the three uploads on your own machine and compare:

| File | Status | `findings` |
| --- | --- | --- |
| `corpus/dev/sqli_01/source.py` | `scanning` | includes `CWE-89` |
| `corpus/dev/bof_01/source.c` | `scanning` | includes `CWE-120` (and a `CWE-119`) |
| `docs/samples/sample.py` | `clean` | `[]` |

A job stuck on `scanning` with `findings: null` means the scan crashed. The API terminal shows the error.

**Windows, C files:** cppcheck installs into `C:\Program Files\Cppcheck`, which is not on `PATH` by default. Add that folder to `PATH` before starting the API, otherwise every C job stays on `scanning` with `findings: null`:

```
$env:PATH = "$env:PATH;C:\Program Files\Cppcheck"
cppcheck --version
python -m uvicorn api.main:app --reload
```