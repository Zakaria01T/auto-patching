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
- `base_url`: the argument of `patcher.generate`, else the `MODEL_BASE_URL` environment variable, else `http://localhost:11434`;
- the model config: `configs/model.yaml`, or the file named by `MODEL_CONFIG` (relative to the repo root). It holds the tag, the temperature and the API.

The config's optional `api` line picks the request `generate` sends:

| `api` | Request | Server |
| --- | --- | --- |
| `"ollama"` (default) | `POST <base_url>/api/chat`, `stream: false` | Ollama |
| `"openai"` | `POST <base_url>/v1/chat/completions`, `stream: false` | vLLM, for example the team's Modal server |

The caller's code does not change between the three places the model can run:

| Where | Config | `base_url` | Used for |
| --- | --- | --- | --- |
| Ollama on a laptop | `configs/model.yaml` (`qwen2.5-coder:7b`) | `http://localhost:11434` (default) | real answers without a GPU server |
| Modal (vLLM, GPU) | `configs/model.modal.yaml` (`Qwen/Qwen2.5-Coder-7B-Instruct`) | the Modal URL, in `MODEL_BASE_URL` | the demo |
| Mock model | either | `http://127.0.0.1:11435` | tests and CI: no GPU, no laptop, same answer every time |

CI never calls a real model. A test that needs a model answer starts the mock in the test itself.

### Run the real model: Ollama on a laptop

```bash
ollama pull qwen2.5-coder:7b
ollama serve
```

`generate(...)` with no `base_url` and no environment variables calls `http://localhost:11434`.

### Run the real model: Modal

```bash
export MODEL_CONFIG=configs/model.modal.yaml
export MODEL_BASE_URL=<the Modal URL, without /v1>
```

The Modal URL is not written in the repo: the repo is public and the server has no API key yet, so anyone with the URL could use the GPU. Ask the person who deployed it. If the server gets a key, put it in `MODEL_API_KEY`; `generate` sends it as a bearer token and never logs it. `generate` never logs the URL either.

The tag must be the name the server gives the model (`GET <base_url>/v1/models`). `Qwen/Qwen2.5-Coder-7B-Instruct` is the prompted model, the one the dev evaluation recommends. The server also has `adapter`.

Measured on 24 November 2026, production prompt:
- **awake:** about 5 s per repair for the prompted model, about 6 s for the adapter;
- **asleep:** the first call took 172 s and 301 s on two tries, while Modal starts a GPU and loads the model. After 150 s Modal answers with a `303` redirect; `generate` follows it. Its default `timeout` is 300 s per wait, so keep it at least that high.

On the 32 dev cases with P1's harness, the Modal server fixed 30/32 with the prompted model and 30/32 with the adapter. The Kaggle run fixed 31/32 for both. The answers differ a little because Modal runs the model in full precision and Kaggle ran it in 4-bit.

With `api: "openai"`, only the generation options `num_predict` (sent as `max_tokens`), `seed` and `top_p` are accepted; others are an error. An answer cut by the token limit (`finish_reason` `length`) is an error, like an Ollama answer that is not `done`.

### Run the mock

```bash
python3 -m patcher.mock_model --mode good
```

Then pass `base_url="http://127.0.0.1:11435"` to `generate`, or set `MODEL_BASE_URL` to it. The mock answers both `/api/chat` and `/v1/chat/completions`, so it works with either config. To switch back to the real model, change `base_url`; nothing else changes.

Each call returns one of four replies:

| Mode | Reply |
| --- | --- |
| `good` | The corrected function in the production layout of `docs/prompting.md`: one code block, `EXPLANATION:`, and `INCLUDES:` for C. It comes from the reviewed repairs in `training/gold.jsonl` (the 8 train functions). For other functions, give `--replies file.json` with `{"function_name": "reply text"}`. A function with no reply is an HTTP 400 error, never a fake fix. |
| `malformed` | Prose and a unified diff, no code block and no `EXPLANATION:`. |
| `empty` | An empty string. |
| `unchanged` | The vulnerable function from the prompt, returned as is, with `EXPLANATION: The function is already safe.` (the base model did this once on the dev cases). |

`--mode malformed,good` uses one mode per call, and the last one repeats. That tests a retry: the first attempt is malformed, the second is good.

The mock answers with the tag it was sent, a complete answer (`done: true`, or `finish_reason: stop`) and zero token counts, so `generate` logs the call as `received_unvalidated`, like a real call. It supports `stream: false` only.

In a test:

```python
from patcher.mock_model import serve

with serve(["malformed", "good"]) as (base_url, model):
    first = generate(..., base_url=base_url)   # malformed reply
    second = generate(..., base_url=base_url)  # good reply
assert len(model.calls) == 2                    # the requests the mock received
```

`serve()` picks a free port, so tests can run in parallel. Tests: `tests/test_mock_model.py`.
