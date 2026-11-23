# Sprint 4 job contract

## 1. Purpose and scope

This is the canonical Sprint 4 wire contract for a job returned by `POST /jobs` or `GET /jobs/{id}`. P2 produces the job and its patch history, P3 supplies validation evidence, and P7 consumes the same snapshot from either endpoint. **Freeze candidate. P2, P3 and P7 approvals are pending.** Section 11 describes the running application. Section 12 records the outstanding approvals and retry-policy question.

## 2. Job lifecycle and status transitions

| Status | Meaning | Permitted next status and condition |
| --- | --- | --- |
| `scanning` | Vulnerability scanning is in progress. Initial status at job creation. | `patching` when the scan completes with findings, `accepted` when all required scanners complete with zero findings, or `needs_human` when the scan fails or is incomplete. |
| `patching` | The remediation model is generating or correcting a patch. | `validating` once P2 supplies a candidate, or `needs_human` if generation cannot safely continue. A further generation call before a candidate exists stays in this state and consumes another attempt. |
| `validating` | The generated patch is undergoing validation. | `accepted` on success, `patching` for another permitted attempt, or `needs_human` when automation cannot safely continue. |
| `accepted` | The patch passed the required validation checks, or the completed initial scan found nothing to patch. | Terminal. |
| `needs_human` | Automated remediation cannot safely complete and requires human review. | Terminal. |

These are the only job status strings. A retry keeps the same job ID. Polls can repeat a state or miss intermediate states. The ordered attempt history survives both. Upload admission precedes this graph. A rejected request returns a 4xx error without creating a job (section 9).

## 3. Job schema

Every job object carries exactly nine keys. The six workflow fields accompany the three existing identity and upload fields.

| Field | JSON type | Meaning and lifecycle |
| --- | --- | --- |
| `id` | string | Stable UUID assigned by the API at creation. Use it for every read and retry. |
| `language` | string | Detected once for an admitted upload, either `python` or `c`. Section 11 covers historical records with a null language. |
| `filename` | string | Original upload basename recorded at creation. |
| `status` | string | Current state from section 2. |
| `findings` | array of finding objects | Starts as `[]`. On scan completion, records the original file's findings. Preserve them across retries. Each item follows the [finding schema](findings.md). |
| `diff` | string or null | Unified diff against the original upload for the current attempt. Null until that attempt has a candidate. For a validated repair this is the exact accepted patch. A zero-finding acceptance keeps it null. |
| `explanation` | string or null | Human-readable reason for the current repair or failure. Null while unavailable. On human review, give the reason automation stopped. |
| `attempts` | array of attempt objects | Starts as `[]`. Contains every generation attempt in order, including failures (section 4). |
| `decision` | string or null | Null throughout processing. At a terminal transition set it to the same literal as `status`, either `accepted` or `needs_human`. |

Existing on-disk metadata such as `created_at`, `message` and the scanner's `error` stays private to the API. The public projection preserves the existing nine keys.

## 4. Attempt log schema

All six keys are required, including keys whose value is null.

| Field | JSON type | Recording rule |
| --- | --- | --- |
| `attempt_number` | integer | Sequential per job, starting at 1. Allocate once, when P2 starts a generation attempt. |
| `raw_model_answer` | string or null | Model response as received, subject to redaction. Preserve malformed text. Null if no response was received. |
| `corrected_function` | string or null | Complete replacement function extracted by P2. Null until extraction succeeds. |
| `diff` | string or null | Unified diff of the candidate against the original source. Null if P2 has yet to produce a usable candidate. |
| `validation_result` | object or null | Null until P3 completes validation of this candidate. P2 attaches the section 5 object to this attempt, including on failure. A generation-only failure keeps null. |
| `timestamp` | string | Attempt start, in ISO 8601 UTC. Accept either `2026-11-23T20:00:00Z` or `2026-11-23T20:00:00+00:00`, with optional fractional seconds. The latter offset matches the generator’s UTC `isoformat()` output. Stable across generation and validation updates. |

Return entries in ascending, contiguous number order even if timestamps coincide. Fill fields on the same entry as data arrives. A model timeout leaves the entry in place with its number, timestamp and null outputs. A parse failure retains the answer and any successfully extracted data. A failed validation retains the candidate and the failed result. P2 records a safe diagnostic in the job explanation when available.

Redact credentials, secrets and sensitive user data from retained answers, diagnostics and API/UI output. Keep the exact original and candidate used for validation in the job's access-controlled workspace. If redaction would change the executable patch, withhold it from unauthorized readers through access control on the job response. An edited display copy cannot stand in for the patch that P3 validated.

## 5. Validation result schema

P3 returns one completed result with exactly six required keys. The job represents an unfinished validation with a null `validation_result`.

| Field | JSON type | Meaning |
| --- | --- | --- |
| `ok` | boolean | True only if every required stage actually ran on this candidate and passed. |
| `failed_step` | string or null | First failing or unverified stage in the order below. Null exactly when `ok` is true. |
| `apply_log` | string | Output from applying the diff to the original source. |
| `test_output` | string | Functional test execution output. |
| `scanner_findings` | array of finding objects | Post-patch findings using the original finding schema. Use `[]` when no findings were returned. |
| `exploit_output` | string | Output from the exploit regression check. |

**Stage vocabulary for agreement.** The job API has no P3 stage enum. Reuse the existing evaluation harness's `git_apply` result and its `functional`, `attack` and `scanner` check names as the four wire values for `failed_step`. Run the stages in the order below.

1. `git_apply` — the exact diff applies to the original and yields P2's preview.
2. `functional` — the required functional tests run and pass.
3. `attack` — the required regression check runs and verifies the patch blocks the previously demonstrated behavior.
4. `scanner` — all configured scanners for the language complete successfully. Compare the original and post-patch sets of `(cwe, rule_id)` pairs for the target CWE. The original set must contain at least one pair, and the two sets must have an empty intersection. A matching pair still blocks clearance after a line move. Return **all** post-patch findings in `scanner_findings`, including those outside the target CWE or from a new rule. Those other findings do not fail this stage on their own. [Harness comparison](../model-compare/run.py)

A failed, skipped, unavailable, timed-out or indeterminate required check yields `ok: false` and the affected stage. P3 may stop at the first failure. Preserve output already available. Use an empty string for absent text and `[]` for absent scanner output. These empty values alone say nothing about success. Record a safe diagnostic in the affected text field where possible. For a scanner execution error, keep only real findings in the array and convey available diagnostic detail in the job explanation through the orchestration context. The section 5 object has no extra diagnostic key.

## 6. P2/P3 module boundary

P2 owns the generation call, extraction, candidate assembly and attempt log. Its inputs are the original upload, its language, the target finding and function, expected behavior, and prior validation feedback on retry. For a corpus case, use its verbatim `test.txt`. For an uploaded file, use nonblank user-supplied behavior text when available, then the target function’s nonblank docstring, then the fixed fallback “Preserve the function’s existing behavior for valid inputs, including its return value and intended side effects.” P2 supplies the first available value to `build_prompts()`. These sources require no new job response key. The fallback guides generation only. P3 still requires executable validation evidence.

The current generator returns raw text. P2 turns a usable response into the following candidate handoff. [Prompt interface](prompting.md)

| Required P2 output | Type | What P3 receives |
| --- | --- | --- |
| `diff` | string | Nonempty unified diff relative to this job's original upload. |
| `patched_preview` | string | Complete patched file text that applying this diff must produce. |
| `attempt_log` | array of section 4 objects | Ordered snapshot of the job's attempts through the candidate. The last entry identifies this attempt, has the same diff and has a null validation result at dispatch. |

P2 persists each attempt, including calls that yield no handoff. P3 receives the three-field handoff in the context of the job ID, original source, original findings, target CWE and required checks. P3 validates that one candidate and returns exactly the six-field result in section 5. It reports an unusable or mismatched supplied patch at `git_apply`.

**P2 owns retry orchestration and job writes.** Bind each P3 call to the dispatched job ID and attempt number outside the result body. P2 attaches the returned result once to that entry and publishes the corresponding state and decision together. Replayed handoffs or callbacks must never append another attempt, overwrite an earlier result, or advance the state of a newer candidate. P3 supplies evidence. P7 reads the persisted outcome.

## 7. P7 integration expectations

Read the job ID from `id`. Poll the job while its status is `scanning`, `patching` or `validating`, including on retry. Stop only at `accepted` or `needs_human`. On a 4xx upload error, show the returned detail and skip polling. A polling timeout is a request-level failure.

Show original findings separately from each attempt's post-patch findings. Present a candidate as awaiting validation until its own result arrives. For `accepted` with a diff, display the validated patch. For `accepted` with a null diff, display “No findings” and omit the patch view. For human review, show the explanation and relevant attempt evidence. Handle null text and empty arrays in every snapshot.

## 8. Nullability and lifecycle rules

- At creation both arrays are empty, and `diff`, `explanation` and `decision` are null. During scanning an empty findings array carries no completion signal.
- On starting a retry, clear the top-level candidate diff and explanation, retain previous attempts, and append the newly numbered entry when generation starts. Once a new candidate exists, publish its diff and available explanation together.
- While validating, the top-level diff equals the candidate attempt's diff. On success, retain it. On human review after validation, retain the last candidate for inspection alongside its unsuccessful result.
- Publish terminal status and matching decision in the same snapshot. An acceptance from `validating` requires an attempt with a diff and a successful result for that exact diff.
- An acceptance directly from `scanning` requires successful completion of all configured scanners with zero findings. Set `status` and `decision` to `accepted`, keep `findings` and `attempts` empty and `diff` null, and explain that the scan found nothing to repair. Skip generation and patch validation. Terminal history is final.

## 9. Error handling and retry semantics

After a failed P3 result, P2 returns the job to `patching` only when the failure is actionable, another generation is safe, and budget remains. Supply the previous result to the next attempt. If validation cannot safely proceed or the budget is exhausted, publish `needs_human` with the reason. A transport failure or malformed P3 reply supplies no trustworthy result. P2 keeps that attempt's result null and closes the validating job as `needs_human` with an explanation.

- **Admission.** Return HTTP 415 for an unsupported file type, 413 for a file over the upload limit, or 422 for a missing file. Return error detail and issue no job ID. No job is persisted or polled.
- **Initial scan.** A completed zero-finding scan ends as specified in section 8. If a required scanner fails or is unavailable, move from `scanning` to `needs_human` with the reason, even if the available findings array is empty.
- **Generation.** Keep each unsuccessful call in the attempt log. Retry in `patching` while safe and within budget. If no candidate can be produced safely, or the budget runs out, move directly to `needs_human` with an explanation. The generation-only attempt retains a null validation result.

## 10. Example job payloads

The first five snapshots follow a repair job through validation and its two alternative outcomes. The sixth shows a separate upload whose initial scan found nothing to repair. Text logs are illustrative.

### New scanning job

```json
{
  "id": "e1b50c4d-77dc-4e00-9368-7b3051700218",
  "status": "scanning",
  "language": "python",
  "filename": "page.py",
  "findings": [],
  "diff": null,
  "explanation": null,
  "attempts": [],
  "decision": null
}
```

### Patching with one attempt in progress

```json
{
  "id": "e1b50c4d-77dc-4e00-9368-7b3051700218",
  "status": "patching",
  "language": "python",
  "filename": "page.py",
  "findings": [
    {
      "file": "page.py",
      "line": 2,
      "cwe": "CWE-79",
      "severity": "medium",
      "rule_id": "python-html-concat",
      "language": "python",
      "owasp": "A03:2021-Injection"
    }
  ],
  "diff": null,
  "explanation": null,
  "attempts": [
    {
      "attempt_number": 1,
      "raw_model_answer": null,
      "corrected_function": null,
      "diff": null,
      "validation_result": null,
      "timestamp": "2026-11-23T20:00:00Z"
    }
  ],
  "decision": null
}
```

### Validating the generated candidate

```json
{
  "id": "e1b50c4d-77dc-4e00-9368-7b3051700218",
  "status": "validating",
  "language": "python",
  "filename": "page.py",
  "findings": [
    {
      "file": "page.py",
      "line": 2,
      "cwe": "CWE-79",
      "severity": "medium",
      "rule_id": "python-html-concat",
      "language": "python",
      "owasp": "A03:2021-Injection"
    }
  ],
  "diff": "--- a/page.py\n+++ b/page.py\n@@ -1,2 +1,3 @@\n def page(name):\n-    return \"<p>\" + name + \"</p>\"\n+    from html import escape\n+    return \"<p>\" + escape(name) + \"</p>\"\n",
  "explanation": "Escape the name before inserting it into HTML.",
  "attempts": [
    {
      "attempt_number": 1,
      "raw_model_answer": "```python\ndef page(name):\n    from html import escape\n    return \"<p>\" + escape(name) + \"</p>\"\n```\nEXPLANATION: Escape the name before inserting it into HTML.",
      "corrected_function": "def page(name):\n    from html import escape\n    return \"<p>\" + escape(name) + \"</p>\"\n",
      "diff": "--- a/page.py\n+++ b/page.py\n@@ -1,2 +1,3 @@\n def page(name):\n-    return \"<p>\" + name + \"</p>\"\n+    from html import escape\n+    return \"<p>\" + escape(name) + \"</p>\"\n",
      "validation_result": null,
      "timestamp": "2026-11-23T20:00:00Z"
    }
  ],
  "decision": null
}
```

### Accepted after all checks passed

```json
{
  "id": "e1b50c4d-77dc-4e00-9368-7b3051700218",
  "status": "accepted",
  "language": "python",
  "filename": "page.py",
  "findings": [
    {
      "file": "page.py",
      "line": 2,
      "cwe": "CWE-79",
      "severity": "medium",
      "rule_id": "python-html-concat",
      "language": "python",
      "owasp": "A03:2021-Injection"
    }
  ],
  "diff": "--- a/page.py\n+++ b/page.py\n@@ -1,2 +1,3 @@\n def page(name):\n-    return \"<p>\" + name + \"</p>\"\n+    from html import escape\n+    return \"<p>\" + escape(name) + \"</p>\"\n",
  "explanation": "Escape the name before inserting it into HTML.",
  "attempts": [
    {
      "attempt_number": 1,
      "raw_model_answer": "```python\ndef page(name):\n    from html import escape\n    return \"<p>\" + escape(name) + \"</p>\"\n```\nEXPLANATION: Escape the name before inserting it into HTML.",
      "corrected_function": "def page(name):\n    from html import escape\n    return \"<p>\" + escape(name) + \"</p>\"\n",
      "diff": "--- a/page.py\n+++ b/page.py\n@@ -1,2 +1,3 @@\n def page(name):\n-    return \"<p>\" + name + \"</p>\"\n+    from html import escape\n+    return \"<p>\" + escape(name) + \"</p>\"\n",
      "validation_result": {
        "ok": true,
        "failed_step": null,
        "apply_log": "Applied page.py.",
        "test_output": "2 tests passed.",
        "scanner_findings": [],
        "exploit_output": "Regression passed."
      },
      "timestamp": "2026-11-23T20:00:00Z"
    }
  ],
  "decision": "accepted"
}
```

### Human review after an unavailable check

```json
{
  "id": "e1b50c4d-77dc-4e00-9368-7b3051700218",
  "status": "needs_human",
  "language": "python",
  "filename": "page.py",
  "findings": [
    {
      "file": "page.py",
      "line": 2,
      "cwe": "CWE-79",
      "severity": "medium",
      "rule_id": "python-html-concat",
      "language": "python",
      "owasp": "A03:2021-Injection"
    }
  ],
  "diff": "--- a/page.py\n+++ b/page.py\n@@ -1,2 +1,3 @@\n def page(name):\n-    return \"<p>\" + name + \"</p>\"\n+    from html import escape\n+    return \"<p>\" + escape(name) + \"</p>\"\n",
  "explanation": "The required regression fixture was unavailable. A reviewer must verify this candidate.",
  "attempts": [
    {
      "attempt_number": 1,
      "raw_model_answer": "```python\ndef page(name):\n    from html import escape\n    return \"<p>\" + escape(name) + \"</p>\"\n```\nEXPLANATION: Escape the name before inserting it into HTML.",
      "corrected_function": "def page(name):\n    from html import escape\n    return \"<p>\" + escape(name) + \"</p>\"\n",
      "diff": "--- a/page.py\n+++ b/page.py\n@@ -1,2 +1,3 @@\n def page(name):\n-    return \"<p>\" + name + \"</p>\"\n+    from html import escape\n+    return \"<p>\" + escape(name) + \"</p>\"\n",
      "validation_result": {
        "ok": false,
        "failed_step": "attack",
        "apply_log": "Applied page.py.",
        "test_output": "2 tests passed.",
        "scanner_findings": [],
        "exploit_output": "Required regression fixture unavailable."
      },
      "timestamp": "2026-11-23T20:00:00Z"
    }
  ],
  "decision": "needs_human"
}
```

### Accepted after a completed scan with zero findings

```json
{
  "id": "0200ddf3-6b45-4a31-81ae-72fff8919d37",
  "status": "accepted",
  "language": "python",
  "filename": "sample.py",
  "findings": [],
  "diff": null,
  "explanation": "The scan completed with no findings.",
  "attempts": [],
  "decision": "accepted"
}
```

## 11. Compatibility requirements

Observed on repository base `9792aad`. Legacy literals below describe existing records and code only. They are outside the Sprint 4 status vocabulary.

| Contract requirement | Current backend implementation | Current UI implementation | Compatibility | Required follow-up and owner |
| --- | --- | --- | --- | --- |
| Stable ID, language, filename and nine public keys | `CONTRACT_FIELDS` and `to_contract` project the same nine keys. POST and GET use the projection. An unknown ID returns 404. | Reads `id` (also tries `job_id`), language and filename from dictionaries. | Keys compatible | P2 and P7 preserve these keys and existing IDs. |
| Start at `scanning` and recognize exactly five statuses | `STATUSES` lists all five plus legacy `uploaded`, `clean` and `rejected`. Supported POST returns `uploaded`; invalid uploads return `rejected` jobs and may have null language. | Displays arbitrary status text. Explicitly handles legacy rejection on POST and GET. | Incompatible | P2 rejects invalid requests with 4xx before creating a job. P7 handles error detail and skips polling. |
| Advance from scan to generation, validation and a terminal decision | A scan with findings stays in `scanning`; zero findings sets `clean`; a crash leaves `scanning` and a private error. No path emits `patching`, `validating`, `accepted` or `needs_human`. | Only `accepted` and `needs_human` of the five have explicit terminal handling. Active states get generic handling. | Missing workflow | P2 wires both acceptance paths and early failures. P7 distinguishes the two accepted outcomes. |
| Always return arrays and poll through active states | Missing keys become null via `meta.get`. Only completed scans store findings. Attempts stay null. | `is_done` stops on *any* findings list, even an initial empty list. Its terminal set also contains `clean` and `rejected`. | Incompatible from first poll | P2 initializes arrays. P7 uses terminal status alone to finish polling. Coordinate rollout. |
| Record candidates, explanations, attempts and decisions | API never fills these fields. The P5 generator returns raw text and can log generation calls. Its call log has a different schema. | Renders metadata and findings. No structured attempt, patch, explanation or decision view. | Missing on both sides | P2 adapts generation output and persists history. P7 consumes the fields. |
| Attach P3's exact result to its matching attempt | Scanner returns finding objects. The job pipeline has no candidate handoff or P3 result producer. The separate model comparison harness has different metrics and acceptance criteria. | No per-attempt validation handling. | Missing integration | P3 supplies the validator, P2 correlates results, P7 displays the evidence. |
| Contract tests and historical records | Existing API tests assert legacy statuses and null attempts. The doc test at the base revision only searched for field and status names, including legacy ones. Stored JSON may omit workflow fields. | Expects scan-only completion and legacy status-specific messages. | Migration required | P2 and P7 agree how to serve or distinguish historical jobs, preserve IDs and metadata, and add Sprint 4 assertions and polling tests before rollout. Never reinterpret a historical zero-finding job as a validated patch. |

Backend and UI evidence: [API projection and endpoints](../api/main.py), [existing API tests](../tests/test_jobs.py), [polling and rendering](../ui/app.py). Earlier [API examples](../api/README.md), [background scan notes](README_background_scan.md) and [sprint handoffs](sprint-detection.md) describe the scan-only behavior.

Module evidence: [generation interface](../patcher/generate.py), [scanner interface](../scanner/scan.py), [evaluation check modes](../model-compare/run.py) and [evaluation metrics](../model-compare/evaluation.py). The evaluation harness scores scanner clearance separately from fix success. Its aggregate success flag cannot certify a job.

## 12. Contract freeze and team sign-off

| Module | Responsibility | Agreement |
| --- | --- | --- |
| P2 | Patch generation and attempt logging | Pending |
| P3 | Patch validation | Pending |
| P7 | Integration and UI/API contract | Pending |

The following decisions require explicit agreement on the reviewed revision:

- **P2 and P7:** Confirm the 4xx admission policy, both accepted payloads and pre-validation failure handling. Agree how existing clients and stored jobs will migrate.
- **P2 and P3:** Agree on the maximum number of attempts, which failures are actionable, and the four stage names, order and pass criteria in section 5.
- **P2, P3 and P7:** Confirm nullable attempt artifacts, the exact-candidate and redaction rules, and the terminal decision strings. Verify that a failed or missing check remains visible to a reviewer.

Record each module owner's explicit approval and the reviewed revision in the pull request before marking its row agreed. Freeze requires all three approvals. Changes to the wire contract after freeze require a reviewed revision and renewed agreement from all three modules. Merge is a separate repository action.
