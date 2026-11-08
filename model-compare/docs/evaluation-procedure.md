# Evaluation procedure

Run all commands from the repository root. Python 3.11+ and Git are required.
No new runtime Python dependencies are needed for the harness. Tests need pytest.
Existing application dependencies remain in `requirements.txt`; scanner package
pins remain in `requirements-scanners.txt`.

## Prepare and inspect DEV

```bash
python3 model-compare/run.py check-dev
python3 -m pytest model-compare/tests -q
```

`check-dev` reads metadata/test specs only and does not execute source code.
Build the image (requires Docker daemon access and package registry access):

```bash
docker build -f model-compare/Dockerfile -t repair-eval:dev .
docker image inspect repair-eval:dev --format '{{.Id}}'
cp model-compare/config.example.json model-compare/config.local.json
```

Replace the image placeholder with the full `sha256:...` ID, and replace model
tags and checkpoint placeholders with the actual installed models. The shared
configuration controls temperature, generation options including optional seed,
inference/check timeouts, scanner profile and execution resource limits. The
image ID pins installed versions even though apt/base-image package resolution
may differ on future builds; archive/export the built image for reproduction.
The image intentionally uses the project's existing scanner package pins.

Install/start Ollama separately and import the fine-tuned checkpoint first.
Inspect the actual served tags and digests:

```bash
curl http://localhost:11434/api/tags
```

Keep tags immutable throughout each run. Preserve the fine-tuning/export metadata
alongside the Ollama digest so the adapter provenance is auditable.

Validate original cases inside containers without requiring a model server:

```bash
python3 model-compare/run.py calibrate-dev --config model-compare/config.local.json
```

For a short infrastructure check, append `--case sqli_01 --case xss_01
--case cmdi_01 --case bof_01`. This creates a DEV calibration artifact, not model
scores. Full model runs always assign the complete selected dataset.

Run the complete DEV comparison:

```bash
python3 model-compare/run.py run --dataset dev \
  --config model-compare/config.local.json \
  --output-dir model-compare/results
```

No host execution fallback exists. Missing models, Docker, scanner tools or image
produce per-case infrastructure records and an incomplete report, not invented
scores. A model inference error counts as a model failure. Run directories use
UTC time plus UUID and are never reused. `journal.jsonl` is appended after each
case so interrupted work retains evidence. Restarting creates a new run; there is
no resume or retry selection that could change denominators.

## Freeze after DEV work

Finish prompt experiments, model selection and assertion validation on DEV.
Commit the implementation and reviewed configuration/provenance where practical.
A freeze does not open the sealed dataset:

```bash
python3 model-compare/run.py freeze \
  --config model-compare/config.local.json \
  --frozen model-compare/frozen.json
```

The freeze command checks the image, versions and actual model identities. It
creates the manifest exclusively and refuses to overwrite an existing file.
Use a new filename after deliberate DEV changes. Reproduce a DEV run with frozen
conditions by adding `--frozen model-compare/frozen.json` to the DEV command.

## Authorized final evaluation — do not run during development

The current `benchmark/` is empty and this command cannot produce final scores
until the sealed cases and reviewed specs are provisioned. Execute **only after
explicit authorization from the evaluation owner**, using frozen conditions:

```bash
python3 model-compare/run.py run --dataset benchmark \
  --authorize-final --frozen model-compare/frozen.json \
  --config model-compare/config.local.json \
  --output-dir model-compare/results
```

The flag is a deliberate operator authorization gate, not an authentication
system. Changes to config, prompt, evaluator, scanner rules or actual environment
invalidate the freeze. Do not inspect failed final cases to tune repairs or select
models; resolve dataset/infrastructure issues through the evaluation owner and
record any authorized rerun transparently.

## Artifacts and troubleshooting

Each `results/<split>/<run-id>/` has `manifest.json`, `journal.jsonl`,
`records.jsonl`, `summary.json`, `summary.csv`, `report.md`, and per-model/per-case
prompt, raw response and extracted patch artifacts. Records include identity,
check evidence, failure reasons, skipped checks and duration. Artifact paths are relative to the run directory. Reports use all
assigned cases. A scanner-persisted finding may coexist with a successful fix.

Exit 2 with INCOMPLETE percentages indicates infrastructure trouble. Inspect
`manifest.json` for preflight errors, then case records for baseline/worker logs.
Check Docker permissions, pinned image availability, tool versions, Ollama URL and
exact digest/tag matches. Baseline normal failures can indicate missing utilities
or incompatible assertion specs. Baseline scanner misses require a documented
scanner-profile decision on DEV; do not count them as repaired cases. C ASan
errors in patched code are model failures, and stdout/status are retained.

This development checkout's `.venv` contains Python 3.12 packages but its Python
launcher resolves to Python 3.14. Tests were therefore run with:

```bash
PYTHONPATH=.venv/lib/python3.12/site-packages /usr/bin/python3.12 -m pytest model-compare/tests -q
```

Prefer a correctly created Python environment for routine use. No model quality
scores are supplied by this implementation change.
