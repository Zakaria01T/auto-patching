from pathlib import Path

import pytest

from patcher.model_input import (
    LineOutsideFunction,
    MultipleMatches,
    NestedDefinition,
    NoEnclosingFunction,
    build_model_input,
)

ROOT = Path(__file__).resolve().parents[1]
DEV = ROOT / "corpus" / "dev"


def _finding(file, line, language="python", cwe="CWE-89", rule_id="test-rule"):
    owasp = None if language == "c" else "A03:2021-Injection"
    return dict(
        file=file,
        line=line,
        cwe=cwe,
        severity="high",
        rule_id=rule_id,
        language=language,
        owasp=owasp,
    )


def _line_containing(source: str, snippet: str) -> int:
    for index, line in enumerate(source.splitlines(), 1):
        if snippet in line:
            return index
    raise AssertionError(f"snippet not found: {snippet!r}")


def test_no_enclosing_function():
    source = "x = 1\n"
    with pytest.raises(NoEnclosingFunction, match=r"empty.py:1: the file has no functions"):
        build_model_input(_finding("empty.py", 1), source)


def test_line_outside_function():
    source = (
        "class C:\n"
        "    flag = True\n"
        "\n"
        "    def method(self):\n"
        "        return 1\n"
    )
    with pytest.raises(LineOutsideFunction, match=r"klass.py:2:"):
        build_model_input(_finding("klass.py", 2), source)


def test_nested_definition():
    source = (
        "def outer():\n"
        "    def inner():\n"
        "        return 1\n"
        "    return inner()\n"
    )
    with pytest.raises(NestedDefinition, match=r"nested.py:3:"):
        build_model_input(_finding("nested.py", 3), source)


def test_multiple_matches():
    source = "int a(void) { return 1; } int b(void) { return 2; }\n"
    with pytest.raises(MultipleMatches, match=r"same.c:1: two or more non-nested functions"):
        build_model_input(_finding("same.c", 1, language="c", cwe="CWE-120"), source)


def _assert_fixture(case_id, filename, language, cwe, vuln_class, snippet, name):
    path = DEV / case_id / filename
    source = path.read_text(encoding="utf-8")
    line = _line_containing(source, snippet)
    result = build_model_input(_finding(filename, line, language, cwe), source)
    assert snippet in result.function_source
    assert name in result.function_source
    assert result.function_source.strip() != snippet.strip()
    assert result.function_name == name
    assert result.language == language
    assert result.cwe == cwe
    assert result.vulnerability_class == vuln_class
    assert result.rule_id == "test-rule"
    assert result.line == line
    return result, source


def test_sqli_01_full_function():
    result, source = _assert_fixture(
        "sqli_01", "source.py", "python", "CWE-89", "sql_injection",
        "username", "get_user",
    )
    assert result.function_source.strip() == (
        "def get_user(conn, username):\n"
        "    query = \"SELECT id, name FROM users WHERE name = '\" + username + \"'\"\n"
        "    return conn.execute(query).fetchall()"
    )
    assert result.context == ""
    assert result.class_name is None
    assert result.function_source in source


def test_xss_01_full_function():
    result, source = _assert_fixture(
        "xss_01", "source.py", "python", "CWE-79", "xss",
        "Hello", "greet_page",
    )
    assert "def greet_page(name):" in result.function_source
    assert result.context == ""
    assert result.function_source in source


def test_cmdi_01_full_function_and_imports():
    result, source = _assert_fixture(
        "cmdi_01", "source.py", "python", "CWE-78", "command_injection",
        "os.system", "ping_host",
    )
    assert "def ping_host(host):" in result.function_source
    assert result.context == "import os"
    assert "import os" in source
    assert result.function_source in source


def test_bof_01_full_function_and_includes():
    result, source = _assert_fixture(
        "bof_01", "source.c", "c", "CWE-120", "buffer_overflow",
        "strcpy", "copy_name",
    )
    assert "void copy_name(const char *input)" in result.function_source
    assert "#include <stdio.h>" in result.context
    assert "#include <string.h>" in result.context
    assert result.function_source.strip().startswith("void copy_name")
    assert "#include" not in result.function_source
    assert result.function_source in source
