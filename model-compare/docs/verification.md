# Implementation verification

Verified on 2026-11-08 in the development checkout. These checks validate the
harness and original case assertions; **they are not model repair scores**.

## Automated tests

```bash
PYTHONPATH=.venv/lib/python3.12/site-packages /usr/bin/python3.12 -m pytest -q
```

Result: **48 passed, 4 skipped**, one existing FastAPI/Starlette deprecation
warning. The existing API TestClient tests required execution outside the Codex
filesystem/network sandbox; an initial sandboxed full run was interrupted when it
stalled. The four skipped tests require scanner tools on the host. The scanners
were subsequently exercised inside the evaluation image during DEV calibration.

After the final metadata symlink guard, the targeted harness suite was rerun:
**33 passed**. `python3 model-compare/run.py check-dev` validated all 32 manifests,
and `git diff --check` passed.

Coverage includes patch failures and valid changes, target checks, all five
metrics, scanner independence, weighted aggregation, both model types, real
artifact/report generation, all-case infrastructure recording, frozen config
drift, final authorization, dataset symlinks, and missing/empty datasets.

## Isolated DEV calibration

Built `model-compare/Dockerfile` from the repository root. Image ID used:

```text
sha256:60b3207cc74d0cc15b7eb73ed9629bb6a95216f9da4ac8d877d2e28a219cbfff
```

The temporary configuration copied `config.example.json` and replaced only the
image ID; model placeholders were unused because calibration does not call a
model server.

```bash
python3 model-compare/run.py calibrate-dev \
  --config /tmp/repair-eval-calibration-config.json
```

Final complete calibration: **32/32 baseline cases passed**, eight per class.
Each case's normal test passed, attack test demonstrated the original vulnerable
behavior, and the original scanner detected the declared CWE.

Evidence in this workspace (runtime artifacts are gitignored):

```text
model-compare/results/dev/calibration-1b88cd551a7f4ca7819c8ad3c82bedb7/calibration.json
```

The artifact records container versions, configuration, evaluator hashes,
per-case stdout/stderr and scanner findings. Earlier failed calibration artifacts
were retained: they exposed non-root tmpfs permissions, ping file capabilities,
and a PIE/ASan startup failure. The fixes were explicit writable tmpfs modes,
unprivileged ping sockets with file capabilities removed, and `gcc -no-pie`.
No retries or case exclusions were used to obtain the final complete calibration.

## Remaining prerequisites

No model inference was performed: supply real installed prompted/fine-tuned
Ollama tags and digests, and preserve adapter training/export provenance. No
quality comparison, Fix Rate, or final benchmark score is claimed.

`benchmark/` is empty. Curators must provision sealed cases with reviewed
assertion specifications, freeze the configuration, and explicitly authorize final
execution. The benchmark command is documented but was not run.
