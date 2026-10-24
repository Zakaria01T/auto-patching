# Auto-patching

Subject 2.3, Automatic Vulnerability Remediation.

## Project structure

```
api/         FastAPI app: jobs, language detection, status
ui/          Streamlit upload and result page
scanner/     SAST tools and the finding format
patcher/     Prompt builder and the Ollama call
sandbox/     Docker image and validation loop
benchmark/   Dev cases now; sealed benchmark in sprint 5
docs/        Business plan and notes
tests/       Automated tests (run by CI)
data/        Runtime data (data/uploads is not committed)
```

Some folders are empty on purpose. Each is filled by the sprint that builds that stage.

## Setup

Requirements: Python 3.11 or newer, and Git.

```bash
git clone https://github.com/Zakaria01T/auto-patching.git
cd auto-patching

python -m venv .venv

# Mac / Linux / Git Bash
source .venv/bin/activate
# Windows PowerShell
.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

Semgrep, Bandit, Flawfinder, and cppcheck are installed separately. Commands and versions are in [docs/scanners.md](docs/scanners.md).

Copy `.env.example` to `.env` and fill in your own values.

## Start the project

Run each command in its own terminal, with the virtual environment active.

**1. API**

```bash
uvicorn api.main:app --reload
```

Check it: open http://localhost:8000/health. It should show `{"status":"ok"}`.

**2. Upload page**

```bash
streamlit run ui/app.py
```

Streamlit prints a local address (usually http://localhost:8501). The upload page should open there.

By default the page calls the API at `http://localhost:8000`, so nothing else is needed when the API runs on your machine with the command above.

**If the API runs elsewhere** (another port or another computer), set `API_URL` before starting Streamlit:

```bash
# Mac / Linux / Git Bash
API_URL=http://host:port streamlit run ui/app.py

# Windows PowerShell
$env:API_URL = "http://host:port"
streamlit run ui/app.py
```

## API (sprint 2: upload and language detection)

Windows PowerShell: use `curl.exe`. On Mac/Linux use `curl`.

### Upload a file

```
curl.exe -F "file=@docs/samples/sample.py" http://localhost:8000/jobs
curl.exe -F "file=@docs/samples/sample.c" http://localhost:8000/jobs
curl.exe -F "file=@docs/samples/notes.txt" http://localhost:8000/jobs
```

Expected: `sample.py` gives `"language":"python"`, `sample.c` gives `"language":"c"`,
and `notes.txt` gives `"status":"rejected"`.

### Read a job

```
curl.exe http://localhost:8000/jobs/<id>
```

An unknown id returns 404.

### Response shape

Every job has exactly nine fields: `id`, `status`, `language`, `filename`,
`findings`, `diff`, `explanation`, `attempts`, `decision`.
In this sprint the last five are always `null`.
Allowed statuses: `uploaded`, `scanning`, `clean`, `patching`, `validating`,
`accepted`, `needs_human`, `rejected`.

## Run the tests

```bash
python -m pytest
```

## LoRA training

LoRA fine-tuning is part of the project: an adapter is trained and compared with the prompted model. Training runs on a free Kaggle notebook (two Tesla T4 GPUs), with Colab as the backup. Details and the checks behind this are in [docs/training.md](docs/training.md) and [docs/costs.md](docs/costs.md).

## Team rules

- Model weights and uploaded files are never committed.
- Add every new package to `requirements.txt` with an exact version (`name==x.y.z`).