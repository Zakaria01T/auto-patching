# Patch service (M2)

`patcher/patch_service.py` calls the model and turns its reply into a validated
corrected function. 

## Usage

````python
from patcher.patch_service import generate_patch

result = generate_patch(finding, vulnerable_function, expected_behavior,
                        db_driver=None, example=None, base_url=..., timeout=300)
````

Extra keyword arguments (`base_url`, `timeout`, `log_path`, `config_path`) go straight
to `patcher.generate.generate`, which builds the p5-v1 prompt and sends the request.

## Result

A successful call returns a `PatchResult`:

| Field | Meaning |
|---|---|
| `corrected_function` | The code from the single fenced block |
| `explanation` | The sentence after `EXPLANATION:` |
| `includes` | C headers from the `INCLUDES:` line (empty tuple for Python) |
| `raw_answer` | The model's reply, untouched, for the attempt log |
| `prompt_version` | `p5-v1` |

## Expected reply layout

````text
```<language>
<one complete corrected function>
```
EXPLANATION: <one sentence>
INCLUDES: <stdio.h>, <string.h>     (optional, C only)
````

## Rejections

Every error inherits from `PatchError` and carries `raw_answer` (`None` for a timeout,
since there was no reply), so the attempt log keeps what the model said.

| Error | Raised when |
|---|---|
| `EmptyReplyError` | The reply is empty or whitespace, or the code block is empty |
| `MalformedReplyError` | No code block, more than one, a wrong language label, `#include` inside a C block, or no `EXPLANATION:` line |
| `UnchangedFunctionError` | The function equals the original (line endings and trailing spaces are ignored) |
| `ModelTimeoutError` | The model call timed out (`TimeoutError`, or a `URLError` wrapping one) |

Other failures (connection refused, wrong model tag, incomplete reply) are not converted;
they propagate unchanged.

## Testing

`tests/test_patch_service.py` runs against the mock model (`patcher/mock_model.py`), so CI
needs no real model.

````
python -m pytest tests/test_patch_service.py
````

## Not covered here

Reinserting the function into the original file, the unified diff, and persisting the
attempt (model tag, prompt version, raw answer, diff, status, attempt number).