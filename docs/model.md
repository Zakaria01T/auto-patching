# Model

This file records the base model of the project, which tags have been run locally through Ollama, and what the first answers looked like.

## Base model: `qwen2.5-coder:7b`

Decided by the team on 3 November 2026. `configs/model.yaml` pins `qwen2.5-coder:7b`; the LoRA adapter is trained on the same base, `Qwen/Qwen2.5-Coder-7B-Instruct`, so the prompted and the fine-tuned model can be compared.

| Item | Value |
| --- | --- |
| Tag | `qwen2.5-coder:7b` |
| Ollama image ID | `dae161e27b0e` |
| Size | 4.7 GB |
| License | Apache-2.0 (the 3B is under the Qwen research license, non-commercial) |

Why the 7B: on the 32 dev cases, asking for the whole fixed file, it fixed 18 against 14 for the 3B, and every answer applied (32 of 32, against 23). It still runs on a laptop CPU, at about 13 to 18 seconds per answer. The LoRA adapter is trained with QLoRA on one Kaggle T4.

```bash
ollama pull qwen2.5-coder:7b
```

The 3B check below is kept as the first record of a tag running locally.

## First tag that was run: `qwen2.5-coder:3b`

| Item | Value |
| --- | --- |
| Tag | `qwen2.5-coder:3b` |
| Ollama image ID | `f72c60cabf62` |
| Size | 1.9 GB |
| Ollama version | 0.40.6 |
| Machine | Intel Core i5-1038NG7, 16 GB RAM, macOS 26.5.2, CPU only |
| Date | 20 October 2026 (first run 19 October) |

Pull and run:

```bash
ollama pull qwen2.5-coder:3b
ollama run qwen2.5-coder:3b "Fix the SQL injection in this Python line and answer with a unified diff: cursor.execute('SELECT * FROM users WHERE name = ' + name)"
```

The answer took 10.2 seconds (second run, so the model was probably already loaded). The first run was not timed.

## What came back

Both runs proposed the safe repair, a parameterized query: `cursor.execute('SELECT * FROM users WHERE name = ?', (name,))`.

Neither run returned a patch that `git apply` accepts:

- First run: plain `-` and `+` lines in a code block, with no file headers and no `@@` hunk header.
- Second run: file headers and a hunk header, but `@@ -1,5 +1,5 @@` does not match the content, and the vulnerable line is kept as context instead of being removed. In a scratch git repository, `git apply --check` failed with `corrupt patch at line 6`.
- Both runs added prose around the diff, and the two answers differ.

This is one prompt on one small input, so it says nothing about a fix rate.

## What this means for the next steps

- The prompt builder has to ask for one exact diff format, with an example, and keep only the diff from the answer.
- A diff that does not apply is a failed attempt, as the plan says.
- Training a model on the exact output format is a good target for the LoRA comparison.

## Where the model runs, and the mock

The pipeline reaches the model through two values only:
- `base_url`, the argument of `patcher.generate`;
- the tag, `model.tag` in `configs/model.yaml`. The temperature also comes from that file.

`generate` sends one Ollama `POST <base_url>/api/chat` request with `stream: false`.

| Where | `base_url` | Used for |
| --- | --- | --- |
| Ollama on a laptop | `http://localhost:11434` (default) | real answers, the demo |
| Mock model | `http://127.0.0.1:11435` | tests and CI: no GPU, no laptop, same answer every time |

CI never calls a real model. A test that needs a model answer starts the mock in the test itself.

### Run the real model

```bash
ollama pull qwen2.5-coder:7b
ollama serve
```

`generate(...)` with no `base_url` calls `http://localhost:11434`.

### Run the mock

```bash
python3 -m patcher.mock_model --mode good
```

Then pass `base_url="http://127.0.0.1:11435"` to `generate`. To switch back to the real model, change `base_url`; nothing else changes.

Each call returns one of four replies:

| Mode | Reply |
| --- | --- |
| `good` | The corrected function in the production layout of `docs/prompting.md`: one code block, `EXPLANATION:`, and `INCLUDES:` for C. It comes from the reviewed repairs in `training/gold.jsonl` (the 8 train functions). For other functions, give `--replies file.json` with `{"function_name": "reply text"}`. A function with no reply is an HTTP 400 error, never a fake fix. |
| `malformed` | Prose and a unified diff, no code block and no `EXPLANATION:`. |
| `empty` | An empty string. |
| `unchanged` | The vulnerable function from the prompt, returned as is, with `EXPLANATION: The function is already safe.` (the base model did this once on the dev cases). |

`--mode malformed,good` uses one mode per call, and the last one repeats. That tests a retry: the first attempt is malformed, the second is good.

The mock answers with the tag it was sent, `done: true` and zero token counts, so `generate` logs the call as `received_unvalidated`, like a real call. It supports `stream: false` only.

In a test:

```python
from patcher.mock_model import serve

with serve(["malformed", "good"]) as (base_url, model):
    first = generate(..., base_url=base_url)   # malformed reply
    second = generate(..., base_url=base_url)  # good reply
assert len(model.calls) == 2                    # the requests the mock received
```

`serve()` picks a free port, so tests can run in parallel. Tests: `tests/test_mock_model.py`.

### Not decided here

A hosted GPU endpoint for the demo. A vLLM server on Modal was tested on 24 November 2026: it answers a production repair prompt in about 5 to 6 seconds once started, but the first call after it sleeps can take minutes. It speaks the OpenAI API (`/v1/chat/completions`), not Ollama's `/api/chat`, and names its models differently, so `generate` cannot call it as is. Using it needs a team decision on the API and the tag.
