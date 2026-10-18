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

## Current Sprint Constraints
For the current sprint, only the following fields are allowed to be populated with data:
* `id`
* `status`
* `language`
* `filename`

The following fields must remain `null` for this sprint:
* `findings`
* `diff`
* `explanation`
* `attempts`
* `decision`
