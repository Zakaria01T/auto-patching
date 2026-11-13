"""Validate every candidate pair in training/c_dataset/candidates/ (run in Docker, network off).

    docker run --rm --network none -v "$PWD":/repo:ro -v "$PWD/training/c_dataset":/work \
        autopatch-casecheck python /work/check.py

For each pair:
1. Scanner: the team scanner (scanner.scan) must report CWE-120 on a line that the
   repair changes. That finding becomes the row's `finding`.
2. Compile vulnerable and repair with gcc -std=c11 -fsanitize=address.
3. Attack: the vulnerable version must stop with an AddressSanitizer error; the repair
   must exit 0 without one.
4. Normal (own cases only, Juliet has no input): both versions exit 0 without an
   AddressSanitizer error and print the same output.
The scanner result on the repair is recorded only: Flawfinder flags some correct fixes.
Writes training/c_dataset/check.json.
"""
import difflib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, "/repo")
from scanner.scan import scan  # noqa: E402

WORK = Path("/work")
SEVERITY = {"high": 3, "medium": 2, "low": 1}


def changed_lines(vuln, repair):
    a, b = vuln.splitlines(), repair.splitlines()
    out = set()
    for tag, i1, i2, _, _ in difflib.SequenceMatcher(None, a, b).get_opcodes():
        if tag != "equal":
            out.update(range(i1 + 1, max(i2, i1 + 1) + 1))
    return out


def run(src, call, tmp, name):
    main = Path(tmp) / f"{name}_main.c"
    main.write_text(f'#include "{src}"\n\nint main(void)\n{{\n    {call};\n    return 0;\n}}\n')
    exe = Path(tmp) / name
    build = subprocess.run(["gcc", "-std=c11", "-D_GNU_SOURCE", "-g", "-O0", "-fsanitize=address",
                            "-fno-omit-frame-pointer", "-w", str(main), "-o", str(exe)],
                           capture_output=True, text=True)
    if build.returncode:
        return {"compiled": False, "error": build.stderr.strip().splitlines()[-1:]}
    try:
        p = subprocess.run([str(exe)], capture_output=True, text=True, timeout=10,
                           env={"ASAN_OPTIONS": "detect_leaks=0"})
    except subprocess.TimeoutExpired:
        return {"compiled": True, "timeout": True, "asan": False, "exit": None, "stdout": ""}
    return {"compiled": True, "asan": "AddressSanitizer" in p.stderr, "exit": p.returncode,
            "stdout": p.stdout[:300]}


def check(d):
    meta = json.loads((d / "meta.json").read_text())
    vuln, repair = d / "vulnerable.c", d / "repair.c"
    res = {"id": meta["id"], "dir": str(d.relative_to(WORK)), "kept": False}
    lines = changed_lines(vuln.read_text(), repair.read_text())
    found = scan(str(vuln), "c")
    hits = [f for f in found if f["cwe"] == "CWE-120" and f["line"] in lines]
    res["scanner_vulnerable"] = [f"{f['cwe']}@{f['line']} {f['severity']} {f['rule_id']}" for f in found]
    res["scanner_repair"] = [f"{f['cwe']}@{f['line']} {f['severity']} {f['rule_id']}"
                             for f in scan(str(repair), "c")]
    if not hits:
        res["reason"] = "scanner does not report CWE-120 on the copy"
        return res
    best = max(hits, key=lambda f: (SEVERITY.get(f["severity"], 0), -f["line"]))
    res["finding"] = {k: best[k] for k in ("line", "cwe", "severity", "rule_id")}
    attack = meta.get("attack_call", meta.get("call"))
    with tempfile.TemporaryDirectory() as tmp:
        res["attack_vulnerable"] = run(vuln, attack, tmp, "va")
        res["attack_repair"] = run(repair, attack, tmp, "ra")
        if "normal_call" in meta:
            res["normal_vulnerable"] = run(vuln, meta["normal_call"], tmp, "vn")
            res["normal_repair"] = run(repair, meta["normal_call"], tmp, "rn")
    va, ra = res["attack_vulnerable"], res["attack_repair"]
    if not (va["compiled"] and ra["compiled"]):
        res["reason"] = "does not compile"
    elif not va["asan"]:
        res["reason"] = "vulnerable version shows no AddressSanitizer error on the attack"
    elif ra["asan"] or ra["exit"] != 0:
        res["reason"] = "repair still fails the attack"
    elif "normal_call" in meta:
        vn, rn = res["normal_vulnerable"], res["normal_repair"]
        if vn.get("asan") or vn.get("exit") != 0:
            res["reason"] = "vulnerable version fails on the normal input"
        elif rn.get("asan") or rn.get("exit") != 0 or rn["stdout"] != vn["stdout"]:
            res["reason"] = "repair changes the normal behaviour"
    if "reason" not in res:
        res["kept"] = True
    return res


def main():
    dirs = sorted(WORK.glob("candidates/juliet_*/")) + sorted(WORK.glob("candidates/own_bof_*/"))
    results = []
    for d in dirs:
        r = check(d)
        results.append(r)
        print(f"{r['id']:45} {'kept' if r['kept'] else 'DROP ' + r['reason']}", flush=True)
    (WORK / "check.json").write_text(json.dumps(results, indent=1))
    for src in ("juliet", "own"):
        sub = [r for r in results if r["id"].startswith(src)]
        print(f"{src}: {sum(r['kept'] for r in sub)}/{len(sub)} kept")


if __name__ == "__main__":
    main()
