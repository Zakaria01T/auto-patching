# Vulnerability repair evaluation methodology

This checkout contained an empty `model-compare/` P6 directory, not an executable
P6 harness. The implementation fills that existing location and reuses
`scanner/scan.py`, its rules, and its Python/C tool selection. Existing API,
scanner and upload workflows are unchanged. `inference.py` is the Ollama adapter;
`run.py` coordinates both model types; `evaluation.py` validates and aggregates;
`worker.py` and `case_checks.py` perform isolated checks.

## Objective and dataset isolation

Compare prompted and fine-tuned repairs under identical evaluation conditions.
`corpus/dev/` contains 32 development cases, eight per class. The `_template` and
`samples` directories are excluded. Each case has `meta.json`, one `source.py` or
`source.c`, `test.txt`, and a reviewed `evaluation.json` linking executable
assertions to the hash of the prose expectations. Source files are authoritative;
no training data is used for evaluation.

DEV supports debugging, prompt experiments and preliminary comparison. Sealed
`benchmark/` is used only after freezing conditions and explicit authorization.
It is currently empty: there is no final dataset or final score in this checkout.
The loader refuses empty datasets, unknown splits, missing assertion specs and
unauthorized benchmark access. A run selects exactly one root; aggregation
rejects mixed splits. Results are stored under separate `dev/` and `benchmark/`
directories. No benchmark cases were executed during implementation.

Before sealing a final dataset, dataset curators must supply reviewed assertion
specifications matching `test.txt`, using the supported scenario contracts in
`case_checks.py` (scenario 1–8 per class). Cases requiring other behavior need
curator-provided assertions and an evaluator freeze **before** model evaluation;
unsupported tests must not be improvised while debugging a sealed evaluation.

## Fair comparison and reproducibility

One configuration lists both model types with separate actual Ollama tags and
checkpoint digests. Both traverse the same `evaluate()` function, prompt template,
generation options, patch validation, case order, scanner configuration, container
image, CPU/memory/PID limits, and timeouts. No retry or best-of-N selection is
performed. Temperature and seed are passed in Ollama options; a seed is not a
promise of bitwise deterministic GPU inference. Both checkpoints must support the
chosen options. Prompt v1 and scanner profile `project-original-v1` are supported;
new profiles require implementation, DEV validation, and a new freeze.

Freeze records the complete config, evaluator/prompt/scanner hashes, image ID,
container tool versions, and actual model metadata. Runs reject changed frozen
conditions. Each run also saves commit, dirty-worktree state, exact dataset hashes,
UTC timestamp, configuration and frozen-file hash. Keep frozen manifests and run
artifacts together. A tag is checked against its digest before and after each
inference; operators must keep the serving instance/checkpoints immutable during
runs. Fine-tuned weights must already be exported/imported into Ollama; training
and adapter conversion are outside this harness. Do not select a checkpoint using
final evaluation outcomes.

## Five metrics

For every class and OVERALL, the denominator is **all assigned cases**, including
invalid generations, inference failures and skipped checks. Overall uses sums of
case counts, never an average of class percentages. Reports include numerator,
denominator, percentage and skipped count for each metric.

1. **Valid Output Rate** = valid outputs / total × 100. Accept exactly one unified
   diff targeting the original source path. Reject empty output, unchanged code,
   malformed diffs, failed `git apply`, extra file changes and unrelated-only
   changes. The patch is applied in a new temporary Git workspace. Python uses AST
   comparison of the named function, ignoring comment/format-only changes. C uses
   the comment/literal-aware tokenized target function body for these simple corpus functions;
   this is not a general C parser. Missing/invalid targets fail validation.
2. **Functional Test Pass Rate** = normal-test passes / total × 100. Normal input
   and expected behavior come from `test.txt`, encoded in reviewed specs and
   assertions. SQL fixtures check returned rows and mutation effects; command
   tests check output/files/status; XSS checks exact expected HTML; C checks exact
   stdout under AddressSanitizer (compiled with `-no-pie` to avoid intermittent PIE/shadow-memory startup failures in containers). Compilation failure fails the check.
3. **Attack Blocked Rate** = blocked attacks / total × 100. SQL uses case-specific
   quote/boolean/multi-row injection and checks unauthorized results or state
   changes. XSS injects `<script>alert(1)</script>` and checks that a literal script
   element is absent. Command injection appends `; touch pwned` and checks that
   the marker does not exist. C supplies 4096 characters (stdin where applicable)
   under AddressSanitizer, requiring a normal exit (including explicit input rejection) and no sanitizer diagnostic.
   These are specific exploit tests, not a proof of general vulnerability absence.
4. **Scanner Rate** = cleared original findings / total × 100. Run the same
   original scanner on original and patched sources. Match original findings by
   declared CWE and rule ID, ignoring shifted line numbers. Every matched
   original rule must disappear. Raw normalized findings are retained. An
   undetected baseline CWE or scanner malfunction is an infrastructure error,
   never an automatic clearance. New findings remain visible in evidence.
5. **Fix Rate** = successful repairs / total × 100. A success is exactly
   `valid_output AND functional_test_pass AND attack_blocked`.
   **Scanner clearance is independent and is not included in Fix Rate.**

A baseline normal pass, exploitable attack, and original scanner finding calibrate
each case before inference. A failed baseline is an infrastructure error. Each
normal, attack and scanner operation uses a new container, preventing state
contamination. Generated execution timeouts fail the corresponding check;
scanner/baseline/container failures are infrastructure errors. Inference failures
are model failures and remain in the denominator. Null checks are explicitly
skipped, not successes. Multiple failure reasons are permitted.

If any assigned case has an infrastructure error, percentages for the entire
comparison are suppressed as INCOMPLETE. Counts and skipped checks remain visible;
fix booleans retain their stated formula. Exit status 2 signals an incomplete run.
Do not quote an incomplete report as a final score.

## Execution boundary and limits

Generated code and exploit payloads execute only in Docker: no network, non-root
UID, read-only root and case mounts, dropped capabilities, no-new-privileges,
limited memory/CPU/PIDs, and disposable work/tmp filesystems. Only trusted worker
files and scanner code are mounted; other datasets and prior results are absent.
Containers are forcibly removed even on timeouts. Host Git handles patches only;
it never imports or executes patched source.

Docker shares a host kernel. Use a dedicated evaluation host/VM for untrusted
models, maintain the container runtime, and retain artifacts for audit. These
assertions assess specified behavior, not arbitrary adversarial test evasion.
