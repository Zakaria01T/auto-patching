"""P5 prompt construction and strict function-response normalization for P1."""
import ast
import difflib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

_RESPONSE = re.compile(
    r"\A\s*```(?P<language>python|c)[ \t]*\n(?P<code>.*?)\n```[ \t]*\n"
    r"EXPLANATION:[ \t]*(?P<explanation>[^\r\n]+)"
    r"(?:\r?\nINCLUDES:[ \t]*(?P<includes>[^\r\n]+))?\s*\Z",
    re.DOTALL,
)
_C_TOKEN = re.compile(
    r'//[^\n]*|/\*.*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|'
    r'[A-Za-z_]\w*|[^\s]',
    re.DOTALL,
)
_C_HEADERS = {
    "assert.h", "ctype.h", "errno.h", "float.h", "limits.h", "locale.h",
    "math.h", "setjmp.h", "signal.h", "stdarg.h", "stdbool.h", "stddef.h",
    "stdint.h", "stdio.h", "stdlib.h", "string.h", "time.h", "wchar.h",
    "wctype.h",
}
_SEVERITY = {"critical": 4, "high": 3, "medium": 2, "low": 1}


class ReplayInputError(ValueError):
    """Saved inference evidence does not match frozen P5 evaluation inputs."""


def extract_target_function(source, language, target):
    """Extract the one top-level target function, excluding surrounding file text."""
    if language == "python":
        node = _python_function(source, target)
        lines = source.splitlines(keepends=True)
        start_line = min([node.lineno, *(d.lineno for d in node.decorator_list)])
        return "".join(lines[start_line - 1:node.end_lineno]).rstrip("\r\n")
    if language == "c":
        start, end, _ = _c_function_span(source, target)
        return source[start:end].strip()
    raise ValueError("unsupported language")


def build_case_prompts(case, original, findings, target):
    """Build the production p5-v1 system/user messages for one DEV case."""
    import sys

    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from patcher.prompts import build_prompts, select_example

    matching = [f for f in findings if f.get("cwe") == case["cwe"]]
    if not matching:
        raise ValueError("original scanner finding for the case CWE is missing")
    finding = sorted(
        matching,
        key=lambda f: (
            -_SEVERITY.get(str(f.get("severity", "")).lower(), 0),
            str(f.get("rule_id", "")),
            int(f.get("line", 0)),
        ),
    )[0]
    # The P1 SQL fixtures run against SQLite even when the function itself does
    # not import sqlite3. Preserve the production prompt's explicit DB context.
    if case["cwe"] == "CWE-89":
        driver, evidence, sql_present = "sqlite3", "P1 DEV SQL fixture uses SQLite", True
    else:
        driver, evidence, sql_present = None, None, None
    example = select_example(finding)
    function = extract_target_function(original, case["language"], target)
    system, user = build_prompts(
        finding,
        function,
        case["test"].read_text(encoding="utf-8"),
        driver,
        example,
        driver_evidence=evidence,
        sql_present=sql_present,
    )
    return {"system": system, "user": user}, {
        "finding": finding,
        "example": example,
    }


def _python_function(source, target, only=False):
    tree = ast.parse(source)
    nodes = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    matching = [n for n in nodes if n.name == target]
    if len(matching) != 1:
        raise ValueError("target function is missing or duplicated")
    if only and (len(tree.body) != 1 or len(nodes) != 1):
        raise ValueError("response must contain exactly the target function")
    return matching[0]


def _python_signature(node):
    return (
        type(node).__name__,
        node.name,
        ast.dump(node.args, include_attributes=False),
        ast.dump(node.returns, include_attributes=False) if node.returns else None,
        node.type_comment,
        [ast.dump(x, include_attributes=False) for x in node.decorator_list],
    )


def _c_tokens(source):
    return [
        m for m in _C_TOKEN.finditer(source)
        if not m.group().startswith(("//", "/*"))
    ]


def _c_function_span(source, target):
    """Return (start, end, header tokens) for one top-level C definition."""
    matches = []
    tokens = _c_tokens(source)
    # Preprocessor directives are file-level boundaries; omit them from the
    # replacement span while retaining their source lines.
    directives = [m.end() for m in re.finditer(r"(?m)^[ \t]*#[^\n]*(?:\n|\Z)", source)]
    depth = 0
    i = 0
    while i < len(tokens):
        token = tokens[i].group()
        if depth == 0 and token == target and i + 1 < len(tokens) and tokens[i + 1].group() == "(":
            parens = 1
            close = i + 2
            while close < len(tokens) and parens:
                value = tokens[close].group()
                parens += (value == "(") - (value == ")")
                close += 1
            if parens == 0:
                body = close
                while body < len(tokens) and tokens[body].group() not in ("{", ";", "="):
                    body += 1
                if body < len(tokens) and tokens[body].group() == "{":
                    brace = 1
                    end = body + 1
                    while end < len(tokens) and brace:
                        value = tokens[end].group()
                        brace += (value == "{") - (value == "}")
                        end += 1
                    if brace:
                        raise ValueError("unbalanced C target function")
                    target_offset = tokens[i].start()
                    last_boundary = max(
                        [0, *(p for p in directives if p <= target_offset)]
                    )
                    prior_depth = 0
                    for prior in tokens[:i]:
                        value = prior.group()
                        if prior_depth == 0 and value in (";", "}"):
                            last_boundary = max(last_boundary, prior.end())
                        prior_depth += (value == "{") - (value == "}")
                    start = last_boundary
                    while start < target_offset and source[start].isspace():
                        start += 1
                    header = tuple(t.group() for t in tokens if start <= t.start() < tokens[body].start())
                    matches.append((start, tokens[end - 1].end(), header))
                    i = end
                    continue
        depth += (token == "{") - (token == "}")
        i += 1
    if len(matches) != 1:
        raise ValueError("source must contain exactly one top-level target function")
    return matches[0]


def _parse_includes(value):
    if value is None:
        return []
    parts = [part.strip() for part in value.split(",")]
    if not parts or any(not re.fullmatch(r"<[A-Za-z0-9_.]+\.h>", p) for p in parts):
        raise ValueError("INCLUDES must list standard <name.h> headers")
    names = [p[1:-1] for p in parts]
    if any(name not in _C_HEADERS for name in names):
        raise ValueError("INCLUDES contains a non-approved standard header")
    if len(set(names)) != len(names):
        raise ValueError("INCLUDES contains duplicate headers")
    return names


def _with_includes(source, names):
    existing = set(re.findall(r"(?m)^\s*#\s*include\s*[<\"]([^>\"]+)[>\"]", source))
    missing = [name for name in names if name not in existing]
    if not missing:
        return source
    lines = source.splitlines(keepends=True)
    last_include = max(
        (i for i, line in enumerate(lines) if re.match(r"^\s*#\s*include\b", line)),
        default=-1,
    )
    insert_at = sum(len(line) for line in lines[:last_include + 1]) if last_include >= 0 else 0
    addition = "".join(f"#include <{name}>\n" for name in missing)
    if insert_at and insert_at < len(source) and source[insert_at] != "\n":
        addition += "\n"
    return source[:insert_at] + addition + source[insert_at:]


def _replace_python(original, code, target):
    old_node = _python_function(original, target)
    new_node = _python_function(code, target, only=True)
    if _python_signature(old_node) != _python_signature(new_node):
        raise ValueError("target function signature or decorators changed")
    old_lines = original.splitlines(keepends=True)
    start_line = min([old_node.lineno, *(d.lineno for d in old_node.decorator_list)])
    end_line = old_node.end_lineno
    start = sum(len(line) for line in old_lines[:start_line - 1])
    end = sum(len(line) for line in old_lines[:end_line])
    suffix = "\n" if end == len(original) or original[end - 1:end] == "\n" else ""
    return original[:start] + code.strip() + suffix + original[end:]


def _replace_c(original, code, target, includes):
    if re.search(r"(?m)^\s*#\s*include\b", code):
        raise ValueError("C fenced function must not contain #include directives")
    updated = _with_includes(original, includes)
    old_start, old_end, old_header = _c_function_span(updated, target)
    new_start, new_end, new_header = _c_function_span(code, target)
    if code[:new_start].strip() or code[new_end:].strip():
        raise ValueError("C response must contain only the target function")
    if old_header != new_header:
        raise ValueError("target C function signature changed")
    function = code[new_start:new_end]
    return updated[:old_start] + function + updated[old_end:]


def function_response_to_diff(raw, original, filename, language, target):
    """Strictly adapt a p5-v1 function response to the unified diff P1 accepts."""
    result = {"raw_format_valid": False, "failure_reasons": [], "patch": ""}
    match = _RESPONSE.fullmatch(raw if isinstance(raw, str) else "")
    if not match:
        result["failure_reasons"].append("invalid_response_format")
        return result
    if match.group("language") != language:
        result["failure_reasons"].append("wrong_fence_language")
        return result
    if not match.group("explanation").strip():
        result["failure_reasons"].append("missing_explanation")
        return result
    try:
        if language == "python":
            if match.group("includes") is not None:
                raise ValueError("INCLUDES is only permitted for C")
            changed = _replace_python(original, match.group("code"), target)
        elif language == "c":
            changed = _replace_c(original, match.group("code"), target, _parse_includes(match.group("includes")))
        else:
            raise ValueError("unsupported language")
    except (SyntaxError, ValueError) as exc:
        result["failure_reasons"].append(str(exc))
        return result
    result["raw_format_valid"] = True
    result["explanation"] = match.group("explanation").strip()
    result["patched_source"] = changed
    result["patch"] = "".join(difflib.unified_diff(
        original.splitlines(keepends=True), changed.splitlines(keepends=True),
        fromfile="a/" + filename, tofile="b/" + filename,
    ))
    return result
