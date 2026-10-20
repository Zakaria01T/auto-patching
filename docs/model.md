# Model

This file records which model tag has been run locally through Ollama, how it ran, and what its first answer looked like.

No model is wired into the pipeline yet, and the base model for the project is not decided. This is a check that one tag runs, not a benchmark.

## Tag that has been run

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

The base model for the product (this 3B tag, a 7B tag on a rented GPU, or another model) and where it is served. That decision is made with P2 and P5.
