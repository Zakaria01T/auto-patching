"""Validate generated Python candidates and add the ones that pass as training rows.

Run from the repository root in the scanner image, network off:
  docker run --rm --network none --user "$(id -u):$(id -g)" -v "$PWD":/repo -w /repo \
      autopatch-casecheck python training/python_dataset/validate.py \
      --source "generated:<model>:<YYYY-MM-DD>" candidates/*.jsonl

Each candidate line is {"class", "vulnerable_code", "repair", "explanation"}.
A candidate becomes a row only if:
  1. both versions parse, and each is one function of at most 30 lines;
  2. the explanation is one sentence of at most 30 words, without hedges;
  3. the project scanner reports the class's CWE on the vulnerable version, and the
     repair no longer reports that rule (pick_finding, as in clean.py);
  4. class checks: command injection repairs keep no shell (shell=True, os.system,
     os.popen, getoutput) and pass no user value where it can be read as an option
     (argument_injection_open); SQL repairs have no quoted placeholder; XSS repairs escape;
  5. the vulnerable function is less than 0.85 similar to corpus/dev, the gold
     cases, benchmark/, every existing row and every row accepted before it.
Accepted rows go to corpus/train/python_<cls>_gNNN/ and training/python_rows.jsonl.
Per-candidate decisions go to training/python_dataset/validate.json.
"""

import argparse
import ast
import json
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (QUOTED_PLACEHOLDER, REPO, SHELL_LEFT, argument_injection_open,  # noqa: E402
                    changed_lines, normalize, pick_finding, reference_cases, scan_files, similarity)

ROWS = REPO / "training" / "python_rows.jsonl"
REPORT = REPO / "training" / "python_dataset" / "validate.json"
TRAIN = REPO / "corpus" / "train"
THRESHOLD = 0.85
CLASSES = {
    "sql_injection": ("sqli", "CWE-89"),
    "command_injection": ("cmdi", "CWE-78"),
    "xss": ("xss", "CWE-79"),
}
HEDGE = re.compile(r"\b(?:though|although|however|but|may|might|cannot|unless|assum\w*|"
                   r"depends?|relies|not shown|unseen)\b", re.IGNORECASE)
ESCAPES = re.compile(r"html\.escape|markupsafe|Markup\.escape|\bescape\(|format_html|"
                     r"bleach\.clean|conditional_escape|autoescape\s*=\s*True")


def one_function(code: str) -> bool:
    tree = ast.parse(code)
    return (len(tree.body) == 1 and isinstance(tree.body[0], (ast.FunctionDef, ast.AsyncFunctionDef))
            and len(code.strip().splitlines()) <= 30)


def static_problem(c: dict) -> str | None:
    if c.get("class") not in CLASSES:
        return "unknown_class"
    for key in ("vulnerable_code", "repair", "explanation"):
        if not isinstance(c.get(key), str) or not c[key].strip():
            return f"missing_{key}"
    try:
        if not (one_function(c["vulnerable_code"]) and one_function(c["repair"])):
            return "not_one_short_function"
    except SyntaxError:
        return "does_not_parse"
    if normalize(c["vulnerable_code"]) == normalize(c["repair"]):
        return "repair_identical"
    e = c["explanation"].strip()
    if (len(re.findall(r"[.!?](?:\s|$)", e)) != 1 or not e.endswith(".")
            or len(e.split()) > 30 or HEDGE.search(e)):
        return "explanation_not_one_plain_sentence"
    if c["class"] == "command_injection" and SHELL_LEFT.search(c["repair"]):
        return "repair_keeps_shell"
    if c["class"] == "command_injection" and argument_injection_open(c["repair"]):
        return "argument_injection_open"
    if c["class"] == "sql_injection" and QUOTED_PLACEHOLDER.search(c["repair"]):
        return "quoted_placeholder_in_sql"
    if c["class"] == "xss" and (not ESCAPES.search(c["repair"]) or ESCAPES.search(c["vulnerable_code"])):
        return "xss_repair_does_not_escape"
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True, help="generated:<model>:<YYYY-MM-DD>")
    ap.add_argument("files", nargs="+")
    args = ap.parse_args()

    cands = []
    for f in args.files:
        for n, line in enumerate(Path(f).read_text().splitlines(), 1):
            if not line.strip():
                continue
            ref = f"{Path(f).parent.name}/{Path(f).name}:{n}"
            try:
                cands.append((ref, json.loads(line)))
            except json.JSONDecodeError:
                cands.append((ref, {"_bad_json": True}))

    report = {}
    statically_ok = []
    for ref, c in cands:
        problem = "bad_json" if c.get("_bad_json") else static_problem(c)
        if problem:
            report[ref] = {"drop": problem}
        else:
            statically_ok.append((ref, c))

    # scan in a temporary folder
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        paths = {}
        for i, (ref, c) in enumerate(statically_ok):
            for kind in ("vulnerable", "repair"):
                p = tmp / f"c{i}_{kind}.py"
                p.write_text(c["vulnerable_code" if kind == "vulnerable" else "repair"].rstrip() + "\n")
                paths[(ref, kind)] = p
        scans = scan_files(list(paths.values()))
        findings = {}
        for ref, c in statically_ok:
            cwe = CLASSES[c["class"]][1]
            f = pick_finding(scans[paths[(ref, "vulnerable")]], scans[paths[(ref, "repair")]],
                             changed_lines(c["vulnerable_code"], c["repair"]), cwe)
            if f is None:
                vuln_cwe = [x for x in scans[paths[(ref, "vulnerable")]] if x["cwe"] == cwe]
                report[ref] = {"drop": "repair_still_flagged" if vuln_cwe else "vulnerable_not_flagged"}
            else:
                findings[ref] = f

    # similarity against references, existing rows and accepted rows
    existing = [json.loads(line) for line in ROWS.read_text().splitlines() if line.strip()]
    pool = list(reference_cases().items())
    pool += [(r["finding"]["file"], normalize(r["vulnerable_code"])) for r in existing]
    counters = {}
    for r in existing:
        m = re.match(r"python_(\w+)_g(\d+)$", r["finding"]["file"].split("/")[2])
        if m:
            counters[m.group(1)] = max(counters.get(m.group(1), 0), int(m.group(2)))

    accepted = []
    for ref, c in statically_ok:
        if ref not in findings:
            continue
        norm = normalize(c["vulnerable_code"])
        best = max(((similarity(norm, other), name) for name, other in pool), default=(0, None))
        if best[0] >= THRESHOLD:
            report[ref] = {"drop": "near_duplicate", "of": best[1], "similarity": round(best[0], 3)}
            continue
        short, cwe = CLASSES[c["class"]]
        counters[short] = counters.get(short, 0) + 1
        cid = f"python_{short}_g{counters[short]:03d}"
        folder = TRAIN / cid
        folder.mkdir()
        (folder / "vulnerable.py").write_text(c["vulnerable_code"].rstrip() + "\n")
        (folder / "repair.py").write_text(c["repair"].rstrip() + "\n")
        source = f"{args.source}:{ref}"
        meta = {"id": cid, "language": "python", "class": c["class"], "cwe": cwe,
                "explanation": c["explanation"].strip(), "source": source, "reviewer": None}
        (folder / "meta.json").write_text(json.dumps(meta, indent=4) + "\n")
        finding = {**findings[ref], "file": f"corpus/train/{cid}/vulnerable.py"}
        accepted.append({"finding": finding, "vulnerable_code": c["vulnerable_code"].rstrip(),
                         "repair": c["repair"].rstrip(), "explanation": c["explanation"].strip(),
                         "source": source, "class": c["class"], "cwe": cwe})
        pool.append((cid, norm))
        report[ref] = {"kept": cid, "closest": [round(best[0], 3), best[1]]}

    with ROWS.open("a") as out:
        for row in accepted:
            out.write(json.dumps(row, ensure_ascii=False) + "\n")

    old = json.loads(REPORT.read_text()) if REPORT.exists() else {}
    old.update(report)
    REPORT.write_text(json.dumps(old, indent=1) + "\n")
    drops = {}
    for v in report.values():
        drops[v.get("drop", "kept")] = drops.get(v.get("drop", "kept"), 0) + 1
    print(f"candidates: {len(cands)}  accepted: {len(accepted)}  {drops}")


if __name__ == "__main__":
    main()
