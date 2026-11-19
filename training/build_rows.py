"""Build and validate the complete training dataset from reviewed source rows.

Run from any directory with ``python training/build_rows.py``. Gold rows are
rebuilt from ``corpus/train/gold_*`` using the project scanner, then combined
with the committed Python and C row files. The build fails on schema/label
errors or exact normalized-function matches against DEV/benchmark.
"""

from __future__ import annotations

import ast
import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
TRAIN = ROOT / "corpus" / "train"
GOLD_OUT = ROOT / "training" / "gold.jsonl"
PYTHON_ROWS = ROOT / "training" / "python_rows.jsonl"
C_ROWS = ROOT / "training" / "c_rows.jsonl"
ROWS_OUT = ROOT / "training" / "rows.jsonl"
REPORT_OUT = ROOT / "training" / "dataset_report.json"

ROW_FIELDS = ("finding", "vulnerable_code", "repair", "explanation", "source", "class", "cwe")
FINDING_FIELDS = ("file", "line", "cwe", "severity", "rule_id", "language", "owasp")
CLASS_CWE = {
    "sql_injection": "CWE-89",
    "xss": "CWE-79",
    "command_injection": "CWE-78",
    "buffer_overflow": "CWE-120",
}
CLASS_LANGUAGE = {
    "sql_injection": "python",
    "xss": "python",
    "command_injection": "python",
    "buffer_overflow": "c",
}
CLASS_OWASP = {
    "sql_injection": "A03:2021-Injection",
    "xss": "A03:2021-Injection",
    "command_injection": "A03:2021-Injection",
    "buffer_overflow": None,
}
GOLD_CASE_IDS = {
    "gold_sqli_01", "gold_sqli_02", "gold_xss_01", "gold_xss_02",
    "gold_cmdi_01", "gold_cmdi_02", "gold_bof_01", "gold_bof_02",
}
ALIASES = {
    "file": ("file", "path", "filename"),
    "line": ("line", "line_number"),
    "cwe": ("cwe", "CWE", "cwe_id"),
    "severity": ("severity",),
    "rule_id": ("rule_id", "rule", "ruleId", "check_id"),
    "language": ("language", "lang"),
    "owasp": ("owasp", "OWASP"),
}
SEVERITY_ALIASES = {
    "critical": "high", "error": "high", "warning": "medium", "info": "low",
}
SEVERITIES = {"high", "medium", "low"}


def _nonempty_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _normalize_cwe(value: Any) -> str:
    text = _nonempty_string(str(value) if isinstance(value, int) else value, "cwe")
    match = re.fullmatch(r"(?:CWE-)?0*(\d+)", text, re.IGNORECASE)
    if not match or int(match.group(1)) < 1:
        raise ValueError(f"invalid CWE value: {value!r}")
    return f"CWE-{int(match.group(1))}"


def normalize_finding(raw: dict[str, Any], row_class: str) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ValueError("finding must be an object")
    finding: dict[str, Any] = {}
    missing = []
    for key, names in ALIASES.items():
        value = next((raw[name] for name in names if name in raw), None)
        if value is None and key not in ("owasp",):
            missing.append(key)
            continue
        if key == "line":
            if isinstance(value, bool):
                raise ValueError("finding.line must be a positive integer")
            try:
                value = int(value)
            except (TypeError, ValueError) as exc:
                raise ValueError("finding.line must be a positive integer") from exc
            if value < 1:
                raise ValueError("finding.line must be a positive integer")
        elif key == "cwe":
            value = _normalize_cwe(value)
        elif key == "severity":
            value = _nonempty_string(value, "finding.severity").lower()
            value = SEVERITY_ALIASES.get(value, value)
            if value not in SEVERITIES:
                raise ValueError(f"unsupported severity: {value!r}")
        elif key == "language":
            value = _nonempty_string(value, "finding.language").lower()
            value = {"py": "python"}.get(value, value)
        elif key == "owasp":
            if value is not None:
                value = _nonempty_string(value, "finding.owasp")
        else:
            value = _nonempty_string(value, f"finding.{key}")
        finding[key] = value
    if missing:
        raise ValueError(f"finding missing required fields: {', '.join(missing)}")
    if finding["language"] != CLASS_LANGUAGE[row_class]:
        raise ValueError(f"{row_class} requires language {CLASS_LANGUAGE[row_class]}")
    if finding["cwe"] != CLASS_CWE[row_class]:
        raise ValueError(f"{row_class} requires finding CWE {CLASS_CWE[row_class]}")
    if finding["owasp"] != CLASS_OWASP[row_class]:
        raise ValueError(f"{row_class} requires OWASP value {CLASS_OWASP[row_class]!r}")
    return finding


def normalize_row(raw: dict[str, Any], *, expected_source: str | None = None) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ValueError("each row must be a JSON object")
    missing = [key for key in ROW_FIELDS if key not in raw]
    if missing:
        raise ValueError(f"row missing required fields: {', '.join(missing)}")
    row_class = _nonempty_string(raw["class"], "class").lower()
    if row_class not in CLASS_CWE:
        raise ValueError(f"unsupported class: {row_class!r}")
    cwe = _normalize_cwe(raw["cwe"])
    if cwe != CLASS_CWE[row_class]:
        raise ValueError(f"{row_class} must use {CLASS_CWE[row_class]}, got {cwe}")
    finding = normalize_finding(raw["finding"], row_class)
    if finding["cwe"] != cwe:
        raise ValueError(f"outer CWE {cwe} does not match finding CWE {finding['cwe']}")
    source = _nonempty_string(raw["source"], "source")
    if expected_source and not source.lower().startswith(expected_source + ":"):
        raise ValueError(f"expected source prefix {expected_source!r}, got {source!r}")
    return {
        "finding": finding,
        "vulnerable_code": _nonempty_string(raw["vulnerable_code"], "vulnerable_code").rstrip(),
        "repair": _nonempty_string(raw["repair"], "repair").rstrip(),
        "explanation": _nonempty_string(raw["explanation"], "explanation"),
        "source": source,
        "class": row_class,
        "cwe": cwe,
    }


def _read_jsonl(path: Path, expected_source: str | None = None) -> list[dict[str, Any]]:
    rows = []
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                raw = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path.relative_to(ROOT)}:{line_number}: invalid JSON: {exc}") from exc
            try:
                rows.append(normalize_row(raw, expected_source=expected_source))
            except ValueError as exc:
                raise ValueError(f"{path.relative_to(ROOT)}:{line_number}: {exc}") from exc
    return rows


def normalize_code(code: str, language: str) -> str:
    """Normalize function/source text for reproducible exclusion comparisons."""
    if language == "python":
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                body = getattr(node, "body", None)
                if (isinstance(body, list) and body and isinstance(body[0], ast.Expr)
                        and isinstance(getattr(body[0], "value", None), ast.Constant)
                        and isinstance(body[0].value.value, str)):
                    body.pop(0)
            code = ast.unparse(tree)
        except (SyntaxError, ValueError):
            pass
        return re.sub(r"\s+", "", code)
    comments = re.compile(r'("(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\')|(/\*.*?\*/|//[^\n]*)', re.S)
    code = comments.sub(lambda match: match.group(1) or "", code)
    code = re.sub(r"^\s*#include.*$", "", code, flags=re.M)
    return re.sub(r"\s+", "", code)


def _c_function_units(code: str) -> list[str]:
    """Extract top-level C function definitions while ignoring braces in literals/comments."""
    token_re = re.compile(r'//[^\n]*|/\*.*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|[A-Za-z_]\w*|[^\s]', re.S)
    tokens = [m for m in token_re.finditer(code) if not m.group().startswith(("//", "/*"))]
    units = []
    brace_depth = 0
    i = 0
    while i < len(tokens):
        token = tokens[i].group()
        if brace_depth == 0 and token == "(" and i > 0 and re.fullmatch(r"[A-Za-z_]\w*", tokens[i - 1].group()):
            paren = 1
            close = i + 1
            while close < len(tokens) and paren:
                value = tokens[close].group()
                paren += (value == "(") - (value == ")")
                close += 1
            if paren == 0:
                body = close
                while body < len(tokens) and tokens[body].group() not in ("{", ";", "=", "}"):
                    body += 1
                if body < len(tokens) and tokens[body].group() == "{":
                    depth = 1
                    end = body + 1
                    while end < len(tokens) and depth:
                        value = tokens[end].group()
                        depth += (value == "{") - (value == "}")
                        end += 1
                    if depth == 0:
                        start_offset = tokens[max(0, i - 2)].start()
                        end_offset = tokens[end - 1].end()
                        units.append(code[start_offset:end_offset])
                        i = end
                        continue
        brace_depth += (token == "{") - (token == "}")
        i += 1
    return units


def normalized_functions(code: str, language: str) -> list[str]:
    """Return normalized function definitions; fall back to a code snippet if needed."""
    if language == "python":
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return [normalize_code(code, language)]
        nodes = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
        if nodes:
            return [normalize_code(ast.unparse(node), language) for node in nodes]
    else:
        units = _c_function_units(code)
        if units:
            return [normalize_code(unit, language) for unit in units]
    return [normalize_code(code, language)]


def _protected_sources() -> list[tuple[str, str, list[str]]]:
    protected = []
    for split, base in (("dev", ROOT / "corpus" / "dev"), ("benchmark", ROOT / "benchmark")):
        if base.is_symlink() or base.resolve() != base.absolute():
            raise ValueError(f"{split} dataset root must not be a symlink")
        for path in sorted(p for p in base.rglob("*") if p.is_file() and p.suffix in (".py", ".c")):
            if path.is_symlink() or not path.resolve().is_relative_to(base.resolve()):
                raise ValueError(f"{split} source escapes dataset root: {path}")
            language = "python" if path.suffix == ".py" else "c"
            rel = path.relative_to(ROOT).as_posix()
            source = path.read_text(encoding="utf-8", errors="replace")
            protected.append((rel, language, normalized_functions(source, language)))
    return protected


def check_exclusions(rows: list[dict[str, Any]]) -> int:
    """Fail if normalized vulnerable code exactly matches a DEV/benchmark source."""
    protected = _protected_sources()
    protected_hashes: dict[tuple[str, str], str] = {}
    for path, language, units in protected:
        for normalized in units:
            if not normalized:
                continue
            digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
            protected_hashes[(language, digest)] = path
    matches = []
    for row in rows:
        language = row["finding"]["language"]
        candidates = normalized_functions(row["vulnerable_code"], language)
        if not candidates or not any(candidates):
            raise ValueError(f"empty normalized function from {row['source']}")
        for candidate in candidates:
            digest = hashlib.sha256(candidate.encode("utf-8")).hexdigest()
            path = protected_hashes.get((language, digest))
            if path:
                matches.append((row["source"], path))
                break
    if matches:
        details = "; ".join(f"{source} exactly matches {path}" for source, path in matches[:10])
        extra = f"; and {len(matches) - 10} more" if len(matches) > 10 else ""
        raise ValueError(f"training data exactly overlaps DEV/benchmark: {details}{extra}")
    return len(protected)


def _scan_gold_file(path: Path, language: str) -> list[dict[str, Any]]:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from scanner import scan

    return scan(str(path), language)


def build_gold_rows(*, scan_file=_scan_gold_file, require_reviewer: bool = False) -> list[dict[str, Any]]:
    rows = []
    for folder in sorted(TRAIN.glob("gold_*")):
        meta = json.loads((folder / "meta.json").read_text(encoding="utf-8"))
        language = meta["language"]
        ext = "py" if language == "python" else "c"
        vulnerable = folder / f"vulnerable.{ext}"
        repair = folder / f"repair.{ext}"
        if require_reviewer and not meta.get("reviewer"):
            raise ValueError(f"{meta['id']}: reviewer is not set")
        findings = scan_file(vulnerable, language)
        candidates = [f for f in findings if f.get("cwe") == meta["cwe"]]
        severity_rank = {"critical": 4, "high": 3, "error": 3, "medium": 2, "warning": 2, "low": 1, "info": 1}
        if not candidates:
            raise ValueError(f"{meta['id']}: scanner did not report {meta['cwe']} on vulnerable file")
        raw_finding = max(candidates, key=lambda f: (severity_rank.get(str(f.get("severity", "")).lower(), 0), -int(f.get("line", 0))))
        rows.append({
            "finding": raw_finding,
            "vulnerable_code": vulnerable.read_text(encoding="utf-8"),
            "repair": repair.read_text(encoding="utf-8"),
            "explanation": meta["explanation"],
            "source": f"gold:corpus/train/{meta['id']}",
            "class": meta["class"],
            "cwe": meta["cwe"],
        })
    if len(rows) != 8:
        raise ValueError(f"expected exactly 8 gold repairs, found {len(rows)}")
    normalized = [normalize_row(row, expected_source="gold") for row in rows]
    _validate_gold_inventory(normalized)
    return normalized


def _validate_gold_inventory(rows: list[dict[str, Any]]) -> None:
    ids = {row["source"].split(":", 1)[1].removeprefix("corpus/train/") for row in rows}
    if ids != GOLD_CASE_IDS:
        missing = sorted(GOLD_CASE_IDS - ids)
        unexpected = sorted(ids - GOLD_CASE_IDS)
        raise ValueError(f"gold inventory mismatch; missing={missing}, unexpected={unexpected}")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _report_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.name


def build_dataset(*, gold_rows: list[dict[str, Any]] | None = None,
                  python_path: Path = PYTHON_ROWS, c_path: Path = C_ROWS,
                  gold_path: Path = GOLD_OUT, rows_path: Path = ROWS_OUT,
                  report_path: Path = REPORT_OUT, require_reviewer: bool = False,
                  refresh_gold: bool = False) -> dict[str, Any]:
    """Refresh gold JSONL, validate all sources, and write rows plus a report."""
    gold_mode = "provided_rows"
    if gold_rows is not None:
        gold_rows = [normalize_row(row, expected_source="gold") for row in gold_rows]
        if len(gold_rows) != 8:
            raise ValueError(f"expected exactly 8 gold repairs, found {len(gold_rows)}")
        _validate_gold_inventory(gold_rows)
    elif refresh_gold:
        gold_rows = build_gold_rows(require_reviewer=require_reviewer)
        gold_mode = "refreshed_with_scanner"
    else:
        gold_rows = _read_jsonl(gold_path, expected_source="gold")
        if len(gold_rows) != 8:
            raise ValueError(f"expected exactly 8 gold repairs in {gold_path}, found {len(gold_rows)}")
        _validate_gold_inventory(gold_rows)
        gold_mode = "validated_committed_gold"
    python_rows = _read_jsonl(python_path)
    c_rows = _read_jsonl(c_path)
    rows = gold_rows + python_rows + c_rows
    protected_count = check_exclusions(rows)
    _write_jsonl(gold_path, gold_rows)
    _write_jsonl(rows_path, rows)

    class_counts = dict(sorted(Counter(row["class"] for row in rows).items()))
    source_counts = dict(sorted(Counter(row["source"].split(":", 1)[0] for row in rows).items()))
    report = {
        "schema_version": 1,
        "row_count": len(rows),
        "gold_row_count": len(gold_rows),
        "gold_input_mode": gold_mode,
        "class_counts": class_counts,
        "source_counts": source_counts,
        "exclusion_check": {
            "method": "SHA-256 of language-specific normalized function definitions; exact matches fail",
            "protected_source_count": protected_count,
            "matched_count": 0,
            "splits": ["corpus/dev", "benchmark"],
        },
        "inputs_sha256": {
            "training/gold.jsonl": _sha256(gold_path),
            _report_path(python_path): _sha256(python_path),
            _report_path(c_path): _sha256(c_path),
        },
        "outputs_sha256": {
            "training/gold.jsonl": hashlib.sha256(gold_path.read_bytes()).hexdigest(),
            _report_path(rows_path): hashlib.sha256(rows_path.read_bytes()).hexdigest(),
        },
    }
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Total rows: {len(rows)}")
    print("Rows per class:")
    for name, count in class_counts.items():
        print(f"  {name}: {count}")
    print("Rows per source:")
    for name, count in source_counts.items():
        print(f"  {name}: {count}")
    print(f"DEV/benchmark exclusion check: passed ({protected_count} protected source files)")
    print(f"Report: {_report_path(report_path)}")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-reviewer", action="store_true", help="require reviewer metadata when refreshing gold")
    parser.add_argument("--refresh-gold", action="store_true", help="regenerate gold rows with the project scanners")
    args = parser.parse_args()
    build_dataset(require_reviewer=args.require_reviewer, refresh_gold=args.refresh_gold)


if __name__ == "__main__":
    main()
