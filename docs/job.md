# Job JSON Shape

This document defines the JSON shape for an Auto-Patching job. P2's API response must strictly match this document. If the code and the document disagree, fix the code or the document the same day.

## Fields
The JSON object must contain exactly the following fields:
* `id`
* `status`
* `language`
* `filename`
* `findings`
* `diff`
* `explanation`
* `attempts`
* `decision`

## Status Lifecycle
The `status` field must strictly use one of the following values, listed in order of the pipeline:
1. `uploaded`
2. `scanning`
3. `clean`
4. `patching`
5. `validating`
6. `accepted`
7. `needs_human`
8. `rejected`

**Warning:** Do not invent or use private status names such as `done` or `ok`.

## Current Wave Constraints
In this wave, only the following fields may be populated with data:
* `id`
* `status`
* `language`
* `filename`
* `findings`

`findings` is `null` until the scan has finished. After that:
* `[]` (an empty list) means the scan found nothing. The status is `clean`.
* A non-empty list means the scan found something. The status stays `scanning`. Each item has the fields defined in `docs/findings.md`.

A rejected upload is never scanned, so its `findings` stays `null`.

If the scan itself crashes, the status stays `scanning` and `findings` stays `null`. This case is not decided yet and may change.

The following fields must remain `null` in this wave:
* `diff`
* `explanation`
* `attempts`
* `decision`

No model is called in this wave, so `patching` is not used yet.