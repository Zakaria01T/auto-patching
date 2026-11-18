"""Helpers shared by the Python dataset scripts: scanning, changed lines, similarity."""

import ast
import difflib
import io
import re
import sys
import tokenize
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
RULES = REPO / "scanner" / "rules"


def scan_files(paths: list[Path], workers: int = 4) -> dict[Path, list[dict]]:
    """Scan Python files with the project scanner (scanner/scan.py), in parallel."""
    sys.path.insert(0, str(REPO))
    from scanner.scan import scan
    with ThreadPoolExecutor(workers) as pool:
        results = pool.map(lambda p: scan(str(p), "python"), paths)
    return dict(zip(paths, results))


def changed_lines(old: str, new: str) -> set[int]:
    """1-based lines of `old` that the repair changes or deletes (an insertion counts
    for the line before it)."""
    lines = set()
    sm = difflib.SequenceMatcher(None, old.splitlines(), new.splitlines(), autojunk=False)
    for tag, i1, i2, _, _ in sm.get_opcodes():
        if tag != "equal":
            lines.update(range(i1 + 1, i2 + 1) if i2 > i1 else {max(i1, 1)})
    return lines


def normalize(code: str) -> str:
    """Code without comments, docstrings and whitespace, for similarity checks."""
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            body = getattr(node, "body", None)
            if (isinstance(body, list) and body and isinstance(body[0], ast.Expr)
                    and isinstance(getattr(body[0], "value", None), ast.Constant)
                    and isinstance(body[0].value.value, str)):
                body.pop(0)
        code = ast.unparse(tree)
    except SyntaxError:
        pass
    out = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(code).readline):
            if tok.type not in (tokenize.COMMENT, tokenize.NL, tokenize.NEWLINE,
                                tokenize.INDENT, tokenize.DEDENT):
                out.append(tok.string)
    except (tokenize.TokenError, IndentationError):
        return re.sub(r"\s+", "", code)
    return "".join(out)


def similarity(a: str, b: str) -> float:
    m = difflib.SequenceMatcher(None, a, b, autojunk=False)
    if m.real_quick_ratio() < 0.85 or m.quick_ratio() < 0.85:
        return m.quick_ratio()
    return m.ratio()


def reference_cases() -> dict[str, str]:
    """Normalized vulnerable code of corpus/dev, the gold cases and benchmark/:
    nothing may be too close to these."""
    refs = {}
    for pattern in ("corpus/dev/*/vulnerable.py", "corpus/train/gold_*/vulnerable.py",
                    "benchmark/**/*.py"):
        for path in REPO.glob(pattern):
            refs[str(path.relative_to(REPO))] = normalize(path.read_text())
    return refs


SEVERITY = {"high": 3, "medium": 2, "low": 1}
SHELL_LEFT = re.compile(
    r"shell\s*=\s*True|os\.system|os\.popen|(?:commands|subprocess)\.get(?:status)?output")
QUOTED_PLACEHOLDER = re.compile(r"'(?:%s|\?|:\w+|\{\w*\})'|%\{\w+\}%")


def pick_finding(vuln: list[dict], repair: list[dict], changed: set[int], cwe: str,
                 prefer_rule: str | None = None) -> dict | None:
    """The finding a repair fixes: the row's CWE on the vulnerable version, with a rule
    the repair no longer reports. Prefers a changed line, then `prefer_rule`, then
    severity, then the team's Semgrep rules over Bandit. None when no finding is fixed."""
    repair_rules = {f["rule_id"] for f in repair}
    candidates = [f for f in vuln if f["cwe"] == cwe and f["rule_id"] not in repair_rules]
    candidates.sort(key=lambda f: (f["line"] not in changed, f["rule_id"] != prefer_rule,
                                   -SEVERITY.get(f["severity"], 0),
                                   not f["rule_id"].startswith("scanner."), f["line"]))
    return candidates[0] if candidates else None


def argument_injection_open(code: str) -> bool:
    """True when a subprocess argument list passes a non-literal value before any "--"
    and the function neither rejects a leading "-" nor checks the value against an
    allow-list (raise ValueError). Such a value can still be read as an option."""
    if re.search(r"startswith\(\s*['\"]-['\"]|raise ValueError", code):
        return False
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return True
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = ast.unparse(node.func)
        if not re.search(r"subprocess\.(?:run|call|check_call|check_output|Popen)$|^(?:run|call|check_output|Popen)$", func):
            continue
        if not node.args or not isinstance(node.args[0], ast.List):
            continue
        elts = node.args[0].elts
        for i, item in enumerate(elts[1:], 1):
            if isinstance(item, ast.Constant):
                if item.value == "--":
                    break
                continue
            prev = elts[i - 1]
            if isinstance(prev, ast.Constant) and str(prev.value).startswith("-"):
                continue  # the value of an option such as -i, -n, -o: never read as one
            if isinstance(item, ast.Call) and ast.unparse(item.func) in ("str", "int") and \
                    item.args and isinstance(item.args[0], ast.Call) and ast.unparse(item.args[0].func) == "int":
                continue  # str(int(x)) is a number
            if isinstance(item, ast.Call) and ast.unparse(item.func) == "str" and item.args and \
                    isinstance(item.args[0], ast.Name) and re.search(
                        rf"\b{item.args[0].id}\s*=\s*int\(", code):
                continue  # str(n) where n = int(...)
            return True
    return False
