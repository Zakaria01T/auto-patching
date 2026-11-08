# Repair comparison results template

Dataset: **DEV / FINAL BENCHMARK (choose exactly one)**
Run ID(s): —; repository commit/dirty state: —; frozen manifest SHA-256: —
Prompt version/hash: —; scanner profile/rule hashes: —; container image ID: —
Ollama/tool versions: —; timestamp: —; hardware/runtime: —
Prompted tag/checkpoint: —; fine-tuned tag/checkpoint/training provenance: —
Shared temperature/seed/generation parameters: —
Shared timeouts/memory/CPU/PID limits: —
Infrastructure complete: —; assigned cases: —; skipped checks: —

| Model | Class | Total | Valid % | Functional % | Attack % | Scanner % | Fix % |
|---|---|---|---|---|---|---|---|
| Prompted | SQL Injection | — | — | — | — | — | — |
| Prompted | XSS | — | — | — | — | — | — |
| Prompted | Command Injection | — | — | — | — | — | — |
| Prompted | Buffer Overflow | — | — | — | — | — | — |
| Prompted | OVERALL | — | — | — | — | — | — |
| Fine-tuned | SQL Injection | — | — | — | — | — | — |
| Fine-tuned | XSS | — | — | — | — | — | — |
| Fine-tuned | Command Injection | — | — | — | — | — | — |
| Fine-tuned | Buffer Overflow | — | — | — | — | — | — |
| Fine-tuned | OVERALL | — | — | — | — | — | — |

Every metric cell must include percentage and numerator/denominator. Overall is
computed from pooled counts. Show INCOMPLETE instead of a percentage whenever
infrastructure is incomplete. DEV is preliminary and cannot be called a final
benchmark score. Empty cells above are placeholders, not measurements.

## Failure analysis

For each model/class list counts and example artifact references for empty/no
change, malformed/non-applicable/wrong-target patches, compilation, functional,
attack/sanitizer failures, inference errors, timeouts and infrastructure errors.
Allow multiple reasons per case. Report scanner persistence independently and
state how many successful fixes retained scanner findings. Explain skipped checks
and all reruns/exclusions; keep all assigned cases in the denominator.

## Interpretation

Fix success is valid AND functional AND attack-blocked. Scanner clearance is a
separate diagnostic. Tests establish the specified cases and exploit payloads,
not universal security or semantic equivalence. Record uncertainty and the small
per-class sample sizes; do not claim statistical significance from percentages
alone. Preserve the complete per-case evidence and manifest with this table.

`run.py run` generates the machine-readable records, CSV counts/percentages/skips
and Markdown comparison automatically. The generated report labels the split and
includes failure counts; complete this narrative with provenance and limitations.
