from urllib.error import URLError

import pytest

from patcher import patch_service
from patcher.mock_model import MALFORMED, layout, serve
from patcher.patch_service import (EmptyReplyError, MalformedReplyError, ModelTimeoutError,
                                   UnchangedFunctionError, generate_patch, parse_reply)

FINDING = dict(file="app/db.py", line=3, cwe="CWE-89", severity="high",
               rule_id="python.sqli", language="python", owasp="A03:2021")
VULNERABLE = '''def get_user(conn, name):
    import sqlite3
    cur = conn.execute("SELECT * FROM users WHERE name = '" + name + "'")
    return cur.fetchall()'''
FIXED = '''def get_user(conn, name):
    import sqlite3
    cur = conn.execute("SELECT * FROM users WHERE name = ?", (name,))
    return cur.fetchall()'''
BEHAVIOR = "get_user returns the rows whose name matches."
GOOD = layout("python", FIXED, "Binds the name as a parameter instead of concatenating it into the SQL.")


def run(mode, **options):
    """One call to generate_patch against the mock server."""
    with serve(mode, replies={"get_user": GOOD}) as (base_url, model):
        result = generate_patch(FINDING, VULNERABLE, BEHAVIOR, base_url=base_url, **options)
        return result, model


# ---- through the mock server (real HTTP path) ----

def test_success():
    result, model = run("good")
    assert result.corrected_function == FIXED
    assert "parameter" in result.explanation
    assert result.raw_answer == GOOD          # raw answer kept
    assert result.prompt_version == "p5-v1"
    assert len(model.calls) == 1


def test_malformed_reply_is_rejected_with_raw_answer():
    with pytest.raises(MalformedReplyError) as error:
        run("malformed")
    assert error.value.raw_answer == MALFORMED


def test_empty_reply_is_rejected():
    with pytest.raises(EmptyReplyError) as error:
        run("empty")
    assert error.value.raw_answer == ""


def test_unchanged_function_is_rejected():
    with pytest.raises(UnchangedFunctionError) as error:
        run("unchanged")
    assert VULNERABLE in error.value.raw_answer


# ---- timeout: the mock has no slow mode, so raise what urllib raises ----

@pytest.mark.parametrize("exc", [TimeoutError("timed out"), URLError(TimeoutError("timed out"))])
def test_timeout(monkeypatch, exc):
    def slow_model(*args, **kwargs):
        raise exc
    monkeypatch.setattr(patch_service, "call_model", slow_model)
    with pytest.raises(ModelTimeoutError) as error:
        generate_patch(FINDING, VULNERABLE, BEHAVIOR)
    assert error.value.raw_answer is None


def test_other_transport_errors_are_not_hidden(monkeypatch):
    def refused(*args, **kwargs):
        raise URLError(ConnectionRefusedError())
    monkeypatch.setattr(patch_service, "call_model", refused)
    with pytest.raises(URLError):
        generate_patch(FINDING, VULNERABLE, BEHAVIOR)


# ---- parser details, no server ----

@pytest.mark.parametrize("reply, error", [
    ("   \n ", EmptyReplyError),
    (None, EmptyReplyError),
    ("```python\n\n```\nEXPLANATION: x", EmptyReplyError),
    (f"```python\n{FIXED}\n```", MalformedReplyError),                                   # no EXPLANATION
    (f"```python\n{FIXED}\n```\nEXPLANATION:   ", MalformedReplyError),                  # empty EXPLANATION
    (f"```python\n{FIXED}\n```\n```python\n{FIXED}\n```\nEXPLANATION: x", MalformedReplyError),  # two blocks
    (f"```java\n{FIXED}\n```\nEXPLANATION: x", MalformedReplyError),                     # wrong label
    (f"```python\n{VULNERABLE}   \r\n```\nEXPLANATION: x", UnchangedFunctionError),     # whitespace only
])
def test_parse_rejects(reply, error):
    with pytest.raises(error):
        parse_reply(reply, VULNERABLE, "python")


def test_parse_c_includes():
    original = "int f(char *s) { char b[8]; strcpy(b, s); return 0; }"
    fixed = "int f(char *s) { char b[8]; strncpy(b, s, 7); b[7] = 0; return 0; }"
    reply = layout("c", fixed, "Bounds the copy.", includes=["<string.h>"])
    result = parse_reply(reply, original, "c")
    assert result.includes == ("<string.h>",)
    assert result.corrected_function == fixed


def test_parse_c_rejects_include_in_block():
    reply = "```c\n#include <string.h>\nint f(void) { return 1; }\n```\nEXPLANATION: x"
    with pytest.raises(MalformedReplyError):
        parse_reply(reply, "int f(void) { return 0; }", "c")