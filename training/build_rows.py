"""Build training/gold.jsonl from corpus/train/gold_*."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRAIN = ROOT / "corpus" / "train"
OUT = ROOT / "training" / "gold.jsonl"

# The seven scanner fields. Adjust ALIASES to the real names in docs/findings.md.
KEYS = ("file", "line", "cwe", "severity", "rule_id", "language", "owasp")
OPTIONAL = {"owasp"}  # Flawfinder and cppcheck return owasp = None
ALIASES = {
    "file": ("file", "path", "filename"),
    "line": ("line", "line_number"),
    "cwe": ("cwe", "CWE", "cwe_id"),
    "severity": ("severity",),
    "rule_id": ("rule_id", "rule", "ruleId", "check_id"),
    "language": ("language", "lang"),
    "owasp": ("owasp", "OWASP"),
}
SEVERITY_RANK = {"critical": 4, "high": 3, "error": 3, "medium": 2, "warning": 2,
                 "low": 1, "info": 1}


def normalize(finding, language, path):
    out, missing = {}, []
    for key in KEYS:
        value = next((finding[a] for a in ALIASES[key] if a in finding), None)
        if key == "language" and value is None:
            value = language
        if key == "file":
            value = str(path)
        if value is None and key not in OPTIONAL:
            missing.append(key)
        out[key] = value
    if missing:
        raise ValueError(f"finding is missing {missing}: {finding}")
    return out


def scan_file(path, language):
    """Return normalized findings from scanner.scan (P3)."""
    for extra in (ROOT, ROOT / "api"):
        if str(extra) not in sys.path:
            sys.path.insert(0, str(extra))
    from scanner import scan  # noqa: E402

    rel = Path(path).resolve().relative_to(ROOT).as_posix()
    return [normalize(f, language, rel) for f in scan(str(path), language)]


def primary_finding(findings, cwe):
    """Highest-severity finding with the given CWE, or None."""
    matches = [f for f in findings if f["cwe"] == cwe]
    if not matches:
        return None
    return max(matches, key=lambda f: (SEVERITY_RANK.get(str(f["severity"]).lower(), 0),
                                       -int(f["line"] or 0)))


def main():
    require_reviewer = "--require-reviewer" in sys.argv
    rows = []
    for d in sorted(TRAIN.glob("gold_*")):
        meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
        ext = "py" if meta["language"] == "python" else "c"
        vuln, repair = d / f"vulnerable.{ext}", d / f"repair.{ext}"
        if require_reviewer and not meta.get("reviewer"):
            sys.exit(f"{meta['id']}: reviewer is not set")
        finding = primary_finding(scan_file(vuln, meta["language"]), meta["cwe"])
        if finding is None:
            sys.exit(f"{meta['id']}: scanner did not report {meta['cwe']} on the vulnerable file")
        rows.append({
            "finding": finding,
            "vulnerable_code": vuln.read_text(encoding="utf-8"),
            "repair": repair.read_text(encoding="utf-8"),
            "explanation": meta["explanation"],
            "source": meta["source"],
            "class": meta["class"],
            "cwe": meta["cwe"],
        })
    if len(rows) != 8:
        sys.exit(f"expected exactly 8 gold repairs, found {len(rows)}")
    OUT.parent.mkdir(exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="\n") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"wrote {len(rows)} rows to {OUT}")


if __name__ == "__main__":
    main()