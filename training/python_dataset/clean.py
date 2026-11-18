"""Clean training/python_rows.jsonl (PR #22 review points 2-4).

Run from the repository root in the scanner image, network off:
  docker run --rm --network none --user "$(id -u):$(id -g)" -v "$PWD":/repo -w /repo \
      autopatch-casecheck python training/python_dataset/clean.py

For every row it:
  1. removes a useless f prefix (an f-string without {}) from the repair;
  2. re-scans both versions with scanner/scan.py and relabels the finding: same CWE,
     rule gone from the repair, preferring a finding on a line the repair changes (command injection
     repairs that keep a shell or leave argument injection open are dropped);
  3. drops repairs whose explanation names a defect (bare scalar instead of a tuple,
     quoted placeholder, table name still formatted, shell=True kept, ...) or whose
     SQL still has a quoted placeholder;
  4. cuts the explanation to its one "The repair ..." sentence, without hedges;
  5. drops rows 0.85 or more similar to corpus/dev, the gold cases or benchmark/;
  6. keeps one row per cluster of near duplicates (0.85), real sources first;
  7. removes the flags field, rewrites meta.json, deletes the folders of dropped rows.
Per-row decisions go to training/python_dataset/clean.json.
"""

import collections
import json
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (QUOTED_PLACEHOLDER, REPO, SHELL_LEFT, argument_injection_open,  # noqa: E402
                    changed_lines, normalize, pick_finding, reference_cases, scan_files, similarity)

ROWS = REPO / "training" / "python_rows.jsonl"
# First version of the PR #22 rows (commit 1c2a952), written by build.sh, for the defect check
ORIGINAL = REPO / "training" / "python_dataset" / "pr22_original_rows.jsonl"
REPORT = REPO / "training" / "python_dataset" / "clean.json"
TRAIN = REPO / "corpus" / "train"
THRESHOLD = 0.85
SOURCE_RANK = {"sven": 0, "crossvul": 1, "cybernative": 2, "synthetic": 3}

DEFECT = re.compile(
    r"\bbut\b|\bremains?\b|\bretains?\b|resembles|bare (?:scalar|string|data|ID)|"
    r"instead of|undefined|not defined|mistakenly|\bomits\b|\bpermits\b|interpolat",
    re.IGNORECASE)
HEDGE = re.compile(r"(?:,? though|, but|,? although)\b.*$|,?\s*(?:and )?(?:complete )?"
                   r"(?:safety )?cannot be (?:verified|confirmed).*$", re.IGNORECASE)
STILL_HEDGED = re.compile(r"though|although|cannot be|unseen|not shown|depends on|relies on",
                          re.IGNORECASE)
UNSAFE_LEFT = re.compile(r"shell\s*=\s*True|os\.system|os\.popen|\.format\(|%\s*\(|\bf['\"]")
FSTRING = re.compile(r"(?<![\w'\"])[fF](?=['\"])((?:'''|\"\"\"|'|\"))(.*?)\1", re.DOTALL)


def case_id(row):
    return row["finding"]["file"].split("/")[2]


def drop_useless_f(code):
    def repl(m):
        return m.group(0) if "{" in m.group(2) else m.group(0)[1:]
    return FSTRING.sub(repl, code)


def repair_sentence(expl):
    sents = re.split(r"(?<=[.!?])\s+(?=[A-Z])", expl.strip())
    hits = [s for s in sents if re.match(r"The (?:repair|fix)\b", s)]
    return hits[0] if hits else None


def short_explanation(sentence):
    text = HEDGE.sub("", sentence).rstrip(" ,;.")
    text = re.sub(r"^The (?:repair|fix)\s+", "", text)
    return text[0].upper() + text[1:] + "."


def main():
    rows = [json.loads(line) for line in ROWS.read_text().splitlines() if line.strip()]
    original = {}
    if ORIGINAL.exists():
        for line in ORIGINAL.read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                original[r["vulnerable_code"].strip()] = r["explanation"]
    decisions = {}
    kept = []

    # 1. useless f prefix
    for row in rows:
        fixed = drop_useless_f(row["repair"])
        if fixed != row["repair"]:
            compile(fixed, "<repair>", "exec")
            row["repair"] = fixed
            path = TRAIN / case_id(row) / "repair.py"
            path.write_text(fixed + ("\n" if path.read_text().endswith("\n") else ""))
            decisions.setdefault(case_id(row), {})["f_prefix_removed"] = True

    # 2. re-scan with the project scanner and relabel the finding: it must have the
    #    row's CWE, its rule gone from the repair, preferably on a changed line
    #    (docs/training.md, Validation step 3)
    paths = [TRAIN / case_id(r) / name for r in rows for name in ("vulnerable.py", "repair.py")]
    scans = scan_files(paths)
    for row in rows:
        cid = case_id(row)
        d = decisions.setdefault(cid, {})
        d["source"] = row["source"].split(":")[0]
        d["class"] = row["class"]
        vuln_text = (TRAIN / cid / "vulnerable.py").read_text()
        rep_text = (TRAIN / cid / "repair.py").read_text()
        changed = changed_lines(vuln_text, rep_text)
        vuln = [f for f in scans[TRAIN / cid / "vulnerable.py"] if f["cwe"] == row["cwe"]]
        rep = scans[TRAIN / cid / "repair.py"]
        d["repair_findings"] = sorted({f["rule_id"] for f in rep})
        old_rule = row["finding"]["rule_id"]
        new = pick_finding(scans[TRAIN / cid / "vulnerable.py"], rep, changed, row["cwe"], old_rule)
        if row["class"] == "command_injection" and SHELL_LEFT.search(row["repair"]):
            d["drop"] = "repair_keeps_shell"
        elif row["class"] == "command_injection" and argument_injection_open(row["repair"]):
            d["drop"] = "argument_injection_open"
        elif not vuln:
            d["drop"] = "no_finding_of_this_cwe_on_vulnerable"
        elif new is None:
            d["drop"] = ("scanner_flags_repair_unsafe" if UNSAFE_LEFT.search(row["repair"])
                         else "scanner_flags_repair_rule_false_positive")
        else:
            if new["rule_id"] != old_rule:
                d["relabelled"] = [old_rule, new["rule_id"]]
            row["finding"] = {**new, "file": row["finding"]["file"]}

        # 3-4. explanation and defects. The long explanation written for PR #22 (the
        #      first version, ORIGINAL) is where defects were named, so it is used for
        #      the defect check when the row came from there.
        long_expl = original.get(row["vulnerable_code"].strip(), row["explanation"])
        evidence = repair_sentence(long_expl) or long_expl
        if repair_sentence(row["explanation"]):
            sentence = repair_sentence(row["explanation"])
        elif len(re.findall(r"[.!?](?:\s|$)", row["explanation"].strip())) == 1:
            sentence = row["explanation"].strip()
        else:
            sentence = None
        if "drop" not in d:
            hedge = HEDGE.search(evidence)
            if sentence is None:
                d["drop"] = "no_repair_sentence"
            elif hedge and DEFECT.search(hedge.group(0)):
                d["drop"] = "explanation_names_defect"
                d["defect"] = hedge.group(0).strip(" ,.")
            elif row["class"] == "sql_injection" and QUOTED_PLACEHOLDER.search(row["repair"]):
                d["drop"] = "quoted_placeholder_in_sql"
        if "drop" not in d:
            short = short_explanation(sentence)
            if STILL_HEDGED.search(short):
                d["drop"] = "explanation_still_hedged"
                d["defect"] = short
            else:
                row["explanation"] = short
                kept.append(row)

    # 5. leakage into dev/gold/benchmark
    refs = reference_cases()
    norm = {case_id(r): normalize(r["vulnerable_code"]) for r in rows}
    survivors = []
    for row in kept:
        cid = case_id(row)
        best = max(((similarity(norm[cid], ref), name) for name, ref in refs.items()),
                   default=(0.0, None))
        decisions[cid]["closest_reference"] = [round(best[0], 3), best[1]]
        if best[0] >= THRESHOLD:
            decisions[cid]["drop"] = "too_close_to_reference"
        else:
            survivors.append(row)

    # 6. near duplicates, real sources first
    survivors.sort(key=lambda r: (SOURCE_RANK.get(r["source"].split(":")[0], 9), case_id(r)))
    final = []
    for row in survivors:
        cid = case_id(row)
        twin = None
        for other in final:
            same_commit = row["source"].startswith("sven:") and row["source"] == other["source"]
            if not same_commit and similarity(norm[cid], norm[case_id(other)]) >= THRESHOLD:
                twin = case_id(other)
                break
        if twin:
            decisions[cid]["drop"] = "near_duplicate"
            decisions[cid]["duplicate_of"] = twin
        else:
            final.append(row)

    # 7. write rows, meta.json, delete dropped folders
    final.sort(key=case_id)
    with ROWS.open("w") as out:
        for row in final:
            row.pop("flags", None)
            out.write(json.dumps(row, ensure_ascii=False) + "\n")
            meta_path = TRAIN / case_id(row) / "meta.json"
            meta = json.loads(meta_path.read_text())
            meta["explanation"] = row["explanation"]
            meta_path.write_text(json.dumps(meta, indent=4, ensure_ascii=False) + "\n")
    for cid, d in decisions.items():
        if "drop" in d:
            shutil.rmtree(TRAIN / cid, ignore_errors=True)

    REPORT.write_text(json.dumps(dict(sorted(decisions.items())), indent=1) + "\n")

    table = collections.Counter((d.get("drop", "kept"), d["class"]) for d in decisions.values())
    print(f"rows in: {len(rows)}  kept: {len(final)}")
    for (what, cls), n in sorted(table.items()):
        print(f"  {what:45} {cls:18} {n}")
    print("kept by source:", dict(collections.Counter(r["source"].split(":")[0] for r in final)))


if __name__ == "__main__":
    main()
