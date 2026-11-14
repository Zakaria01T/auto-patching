"""Deduplicate the validated pairs and export them in P4's schema (docs/training.md).

    python3 training/c_dataset/export.py

Reads check.json, compares every vulnerable function with the other kept pairs and with
corpus/dev/, the gold repairs in corpus/train/ and benchmark/, copies the kept pairs to
corpus/train/<id>/, then writes training/c_rows.jsonl and training/c_dataset/dedupe.json.
"""
import difflib
import hashlib
import json
import re
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
SIMILAR = 0.85  # difflib ratio on normalized code: at or above counts as a match


def normalize(code):
    code = re.sub(r"/\*.*?\*/|//[^\n]*", "", code, flags=re.S)
    code = re.sub(r"^\s*#include.*$", "", code, flags=re.M)
    return re.sub(r"\s+", "", code)


def protected():
    """Code the training rows must not match: dev cases, gold repairs, benchmark."""
    out = {}
    for pattern in ("corpus/dev/*/source.*", "corpus/train/gold_*/vulnerable.*", "benchmark/**/*.c",
                    "benchmark/**/*.py"):
        for f in REPO.glob(pattern):
            out[str(f.relative_to(REPO))] = normalize(f.read_text(encoding="utf-8", errors="replace"))
    return out


def main():
    checks = json.loads((HERE / "check.json").read_text())
    guard = protected()
    train = REPO / "corpus" / "train"
    for old in list(train.glob("juliet_*")) + list(train.glob("own_bof_*")):
        shutil.rmtree(old)
    seen, rows, log = {}, [], []
    for r in checks:
        if not r["kept"]:
            continue
        d = HERE / r["dir"]
        vuln = (d / "vulnerable.c").read_text()
        norm = normalize(vuln)
        digest = hashlib.sha256(norm.encode()).hexdigest()
        entry = {"id": r["id"], "kept": False}
        closest = max(((difflib.SequenceMatcher(None, norm, g).ratio(), p) for p, g in guard.items()),
                      default=(0.0, None))
        entry["closest_protected"] = {"path": closest[1], "ratio": round(closest[0], 2)}
        if digest in seen:
            entry["reason"] = f"duplicate of {seen[digest]}"
        elif closest[0] >= SIMILAR:
            entry["reason"] = f"matches {closest[1]} (ratio {closest[0]:.2f})"
        else:
            seen[digest] = r["id"]
            entry["kept"] = True
            meta = json.loads((d / "meta.json").read_text())
            shutil.copytree(d, train / r["id"])
            rows.append({
                "finding": {"file": f"corpus/train/{r['id']}/vulnerable.c", **r["finding"],
                            "language": "c", "owasp": None},
                "vulnerable_code": vuln,
                "repair": (d / "repair.c").read_text(),
                "explanation": meta["explanation"],
                "source": meta["source"],
                "class": "buffer_overflow",
                "cwe": "CWE-120",
            })
        log.append(entry)
    keys = ("file", "line", "cwe", "severity", "rule_id", "language", "owasp")
    for row in rows:  # same key order as training/gold.jsonl
        row["finding"] = {k: row["finding"][k] for k in keys}
    with (REPO / "training" / "c_rows.jsonl").open("w", encoding="utf-8", newline="\n") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    (HERE / "dedupe.json").write_text(json.dumps(log, indent=1))
    print(f"validated {len(log)}, exported {len(rows)} rows to training/c_rows.jsonl")
    for e in log:
        if not e["kept"]:
            print(f"  dropped {e['id']}: {e['reason']}")
    top = sorted(log, key=lambda e: -e["closest_protected"]["ratio"])[:5]
    print("closest to protected code:", [(e["id"], e["closest_protected"]) for e in top])


if __name__ == "__main__":
    main()
