import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_rows import ROOT, scan_file

for d in sorted((ROOT / "corpus" / "train").glob("gold_*")):
    lang, ext = ("c", "c") if "bof" in d.name else ("python", "py")
    for name in ("vulnerable", "repair"):
        print(f"== {d.name} {name}")
        for f in scan_file(d / f"{name}.{ext}", lang):
            print("  ", f["cwe"], f["rule_id"], "line", f["line"], f["severity"])