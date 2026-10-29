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


@pytest.mark.skipif(not _python_tools_ready(), reason="follow docs/scanners.md to install Semgrep and Bandit")
def test_safe_python_sample_is_empty():
    assert scan("docs/samples/sample.py", "python") == []
