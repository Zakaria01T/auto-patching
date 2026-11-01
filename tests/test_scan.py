import pytest

from scanner.scan import _merge, _tool, scan


def _python_tools_ready() -> bool:
    try:
        _tool("semgrep")
        _tool("bandit")
    except FileNotFoundError:
        return False
    return True


def test_scan_can_be_imported():
    from scanner import scan as imported

    assert imported is scan


def test_same_line_and_cwe_is_one_finding():
    merged = _merge(
        [
            {
                "file": "",
                "line": 2,
                "cwe": "CWE-89",
                "severity": "medium",
                "rule_id": "B608",
                "language": "python",
                "owasp": "A03:2021-Injection",
            },
            {
                "file": "",
                "line": 2,
                "cwe": "CWE-89",
                "severity": "high",
                "rule_id": "python-sql-string-concat",
                "language": "python",
                "owasp": "A03:2021-Injection",
            },
        ],
        "app.py",
    )
    assert len(merged) == 1
    assert merged[0]["file"] == "app.py"
    assert merged[0]["severity"] == "high"
    assert list(merged[0]) == [
        "file", "line", "cwe", "severity", "rule_id", "language", "owasp",
    ]


def _c_tools_ready() -> bool:
    try:
        _tool("flawfinder")
        _tool("cppcheck")
    except FileNotFoundError:
        return False
    return True


def _cwes(path: str, language: str) -> set[str]:
    return {item["cwe"] for item in scan(path, language)}


@pytest.mark.skipif(not _python_tools_ready(), reason="follow docs/scanners.md to install Semgrep and Bandit")
def test_safe_python_sample_is_empty():
    assert scan("docs/samples/sample.py", "python") == []


@pytest.mark.skipif(not _python_tools_ready(), reason="follow docs/scanners.md to install Semgrep and Bandit")
def test_sqli_01_returns_cwe_89():
    assert "CWE-89" in _cwes("corpus/dev/sqli_01/source.py", "python")


@pytest.mark.skipif(not _python_tools_ready(), reason="follow docs/scanners.md to install Semgrep and Bandit")
def test_xss_01_returns_cwe_79():
    assert "CWE-79" in _cwes("corpus/dev/xss_01/source.py", "python")


@pytest.mark.skipif(not _python_tools_ready(), reason="follow docs/scanners.md to install Semgrep and Bandit")
def test_cmdi_01_returns_cwe_78():
    assert "CWE-78" in _cwes("corpus/dev/cmdi_01/source.py", "python")


@pytest.mark.skipif(not _c_tools_ready(), reason="follow docs/scanners.md to install Flawfinder and cppcheck")
def test_bof_01_returns_cwe_120():
    assert "CWE-120" in _cwes("corpus/dev/bof_01/source.c", "c")
