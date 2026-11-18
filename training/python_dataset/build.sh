#!/usr/bin/env bash
# Rebuild training/python_rows.jsonl and corpus/train/python_* from the PR #22 rows
# (commit 1c2a952) plus the generated candidates. Run from the repository root.
# Needs the autopatch-casecheck image (docs/training.md). Overwrites the Python rows.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
D=training/python_dataset
run() {
  docker run --rm --network none --user "$(id -u):$(id -g)" -v "$PWD":/repo -w /repo \
    autopatch-casecheck python "$@"
}
git checkout 1c2a952 -- training/python_rows.jsonl corpus/train
rm -rf corpus/train/python_*_g[0-9]* "$D/validate.json"
run "$D/clean.py"
run "$D/validate.py" --source "generated:opencode/deepseek-v4.1-flash-free:2026-11-18" \
  "$D/candidates/xss-01.jsonl" "$D/candidates/cmdi-01.jsonl"
run "$D/validate.py" --source "generated:openrouter/nvidia/nemotron-3-ultra-550b-a55b:free:2026-11-18" \
  "$D/candidates/xss-02.jsonl"
run "$D/validate.py" --source "generated:opencode/deepseek-v4.1-flash-free:2026-11-18" \
  "$D/candidates/xss-03.jsonl" "$D/candidates/cmdi-02.jsonl"
rm -rf "$D/__pycache__"
