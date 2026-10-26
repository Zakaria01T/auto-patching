"""Run the scanners from docs/scanners.md and return finding objects."""

import csv
import io
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RULES = Path(__file__).resolve().parent / "rules"

FIELDS = ("file", "line", "cwe", "severity", "rule_id", "language", "owasp")
SEVERITY_RANK = {"high": 3, "medium": 2, "low": 1}

OWASP_BY_CWE = {
    "CWE-89": "A03:2021-Injection",
    "CWE-79": "A03:2021-Injection",
    "CWE-78": "A03:2021-Injection",
}

_CWE_TEXT = re.compile(r"CWE-(\d+)", re.IGNORECASE)


def scan(path: str, language: str) -> list[dict]:
    """Scan one file. Python uses Semgrep and Bandit. C uses Flawfinder and cppcheck."""
    lang = _language(language)
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(path)

    target = _with_suffix(source, ".py" if lang == "python" else ".c")
    try:
        if lang == "python":
            findings = _semgrep(target, lang) + _bandit(target, lang)
        else:
            findings = _flawfinder(target, lang) + _cppcheck(target, lang)
    finally:
        if target != source:
            target.unlink(missing_ok=True)

    return _merge(findings, Path(path).name)


def _language(language: str) -> str:
    name = language.strip().lower()
    if name in {"python", "py"}:
        return "python"
    if name == "c":
        return "c"
    raise ValueError(f"unsupported language: {language}")


def _with_suffix(source: Path, suffix: str) -> Path:
    if source.suffix == suffix:
        return source
    handle = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    try:
        handle.write(source.read_bytes())
    finally:
        handle.close()
    return Path(handle.name)


def _bindir() -> Path | None:
    for folder in (REPO / ".venv-scanners" / "bin", REPO / ".venv-scanners" / "Scripts"):
        if folder.is_dir():
            return folder
    return None


def _tool(name: str) -> str:
    folder = _bindir()
    if folder is not None:
        for candidate_name in (name, name + ".exe"):
            candidate = folder / candidate_name
            if candidate.is_file() and os.access(candidate, os.X_OK):
                return str(candidate)
    found = shutil.which(name)
    if found:
        return found
    raise FileNotFoundError(f"{name} is not installed. Follow docs/scanners.md.")


def _env() -> dict[str, str]:
    env = os.environ.copy()
    folder = _bindir()
    if folder is not None:
        env["PATH"] = str(folder) + os.pathsep + env.get("PATH", "")
    return env


def _run(argv: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv,
        capture_output=True,
        text=True,
        env=_env(),
        timeout=120,
    )


def _finding(line, cwe, severity, rule_id, language, owasp) -> dict:
    return {
        "file": "",
        "line": int(line),
        "cwe": cwe,
        "severity": severity,
        "rule_id": rule_id,
        "language": language,
        "owasp": owasp,
    }


def _cwe_name(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, int):
        return f"CWE-{value}" if value > 0 else None
    if isinstance(value, list):
        for item in value:
            name = _cwe_name(item)
            if name:
                return name
        return None
    text = str(value).strip()
    if text.isdigit():
        number = int(text)
        return f"CWE-{number}" if number > 0 else None
    match = _CWE_TEXT.search(text)
    if not match or match.group(1) == "0":
        return None
    return f"CWE-{int(match.group(1))}"


def _owasp(cwe: str | None, metadata: dict | None = None) -> str | None:
    if metadata:
        raw = metadata.get("owasp")
        if isinstance(raw, list):
            raw = raw[0] if raw else None
        if isinstance(raw, str) and raw.strip():
            return raw.strip()
    if cwe is None:
        return None
    return OWASP_BY_CWE.get(cwe)


def _severity_semgrep(value: str) -> str:
    name = (value or "").upper()
    if name == "ERROR":
        return "high"
    if name == "WARNING":
        return "medium"
    return "low"


def _severity_bandit(value: str) -> str:
    name = (value or "").lower()
    if name in SEVERITY_RANK:
        return name
    return "low"


def _severity_flawfinder(level: str) -> str:
    try:
        number = int(level)
    except (TypeError, ValueError):
        return "low"
    if number >= 4:
        return "high"
    if number >= 2:
        return "medium"
    return "low"


def _severity_cppcheck(value: str) -> str:
    name = (value or "").lower()
    if name == "error":
        return "high"
    if name == "warning":
        return "medium"
    return "low"


def _semgrep(path: Path, language: str) -> list[dict]:
    import json

    proc = _run([
        _tool("semgrep"),
        "scan",
        "--metrics=off",
        "--disable-version-check",
        "--quiet",
        "--json",
        "--config",
        str(RULES),
        str(path),
    ])
    try:
        payload = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise RuntimeError(proc.stderr.strip() or "semgrep did not return JSON") from exc
    errors = payload.get("errors") or []
    if errors:
        message = errors[0].get("message") if isinstance(errors[0], dict) else str(errors[0])
        raise RuntimeError(message or "semgrep failed")

    findings = []
    for hit in payload.get("results") or []:
        extra = hit.get("extra") or {}
        metadata = extra.get("metadata") or {}
        cwe = _cwe_name(metadata.get("cwe"))
        findings.append(_finding(
            hit.get("start", {}).get("line", 0),
            cwe,
            _severity_semgrep(extra.get("severity", "")),
            hit.get("check_id") or "",
            language,
            _owasp(cwe, metadata),
        ))
    return findings


def _bandit(path: Path, language: str) -> list[dict]:
    import json

    proc = _run([_tool("bandit"), "-q", "-f", "json", str(path)])
    try:
        payload = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise RuntimeError(proc.stderr.strip() or "bandit did not return JSON") from exc

    findings = []
    for hit in payload.get("results") or []:
        cwe_info = hit.get("issue_cwe") or {}
        cwe = _cwe_name(cwe_info.get("id") if isinstance(cwe_info, dict) else cwe_info)
        findings.append(_finding(
            hit.get("line_number", 0),
            cwe,
            _severity_bandit(hit.get("issue_severity", "")),
            hit.get("test_id") or "",
            language,
            _owasp(cwe),
        ))
    return findings


def _flawfinder(path: Path, language: str) -> list[dict]:
    proc = _run([_tool("flawfinder"), "--quiet", "--csv", str(path)])
    if proc.returncode != 0 and not proc.stdout.strip():
        raise RuntimeError(proc.stderr.strip() or "flawfinder failed")
    findings = []
    for row in csv.DictReader(io.StringIO(proc.stdout)):
        cwe = _cwe_name(row.get("CWEs"))
        if not row.get("Line"):
            continue
        findings.append(_finding(
            row["Line"],
            cwe,
            _severity_flawfinder(row.get("Level", "")),
            row.get("RuleId") or row.get("Name") or "",
            language,
            _owasp(cwe),
        ))
    return findings


def _cppcheck(path: Path, language: str) -> list[dict]:
    proc = _run([
        _tool("cppcheck"),
        "-q",
        "--enable=warning",
        "--template={file}\t{line}\t{severity}\t{id}\t{cwe}\t{message}",
        str(path),
    ])
    # cppcheck writes the template to stderr.
    text = "\n".join(part for part in (proc.stdout, proc.stderr) if part)
    findings = []
    for line in text.splitlines():
        parts = line.split("\t")
        if len(parts) < 5 or parts[3] == "checkersReport":
            continue
        cwe = _cwe_name(parts[4])
        findings.append(_finding(
            parts[1],
            cwe,
            _severity_cppcheck(parts[2]),
            parts[3],
            language,
            _owasp(cwe),
        ))
    if proc.returncode != 0 and not findings:
        raise RuntimeError(proc.stderr.strip() or "cppcheck failed")
    return findings


def _merge(findings: list[dict], filename: str) -> list[dict]:
    kept: dict[tuple, dict] = {}
    for item in findings:
        item["file"] = filename
        key = (item["file"], item["line"], item["cwe"])
        current = kept.get(key)
        if current is None or SEVERITY_RANK[item["severity"]] > SEVERITY_RANK[current["severity"]]:
            kept[key] = item
    ordered = sorted(kept.values(), key=lambda item: (item["line"], item["cwe"] or "", item["rule_id"]))
    return [{field: item[field] for field in FIELDS} for item in ordered]
