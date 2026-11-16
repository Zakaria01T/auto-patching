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

## Not decided here

Where the model is served for the demo (laptop CPU or a rented GPU).
