#!/usr/bin/env bash
# Rebuild training/python_rows.jsonl and corpus/train/python_* from the PR #22 rows
# (commit 2cc6bca) plus the generated candidates. Run from the repository root.
# Needs the autopatch-casecheck image (docs/training.md). Overwrites the Python rows.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
D=training/python_dataset
run() {
  docker run --rm --network none --user "$(id -u):$(id -g)" -v "$PWD":/repo -w /repo \
    autopatch-casecheck python "$@"
}
BASE=2cc6bca      # PR #22 rows after Zakaria's own cleaning
FIRST=1c2a952     # first PR #22 rows, whose long explanations name the defects
rm -rf corpus/train/python_* "$D/validate.json"
git checkout "$BASE" -- training/python_rows.jsonl corpus/train
git show "$FIRST:training/python_rows.jsonl" > "$D/pr22_original_rows.jsonl"
run "$D/clean.py"
rm -f "$D/pr22_original_rows.jsonl"
run "$D/validate.py" --source "generated:opencode/deepseek-v4.1-flash-free:2026-11-18" \
  "$D/candidates/xss-01.jsonl" "$D/candidates/cmdi-01.jsonl"
run "$D/validate.py" --source "generated:openrouter/nvidia/nemotron-3-ultra-550b-a55b:free:2026-11-18" \
  "$D/candidates/xss-02.jsonl"
run "$D/validate.py" --source "generated:opencode/deepseek-v4.1-flash-free:2026-11-18" \
  "$D/candidates/xss-03.jsonl" "$D/candidates/cmdi-02.jsonl"
rm -rf "$D/__pycache__"
