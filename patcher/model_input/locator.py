"""Locate the unique non-nested function that contains a 1-based finding line."""

import ast

from .errors import (
    LineOutsideFunction,
    MultipleMatches,
    NestedDefinition,
    NoEnclosingFunction,
)
from .types import LocatedFunction

_C_KEYWORDS = {
    "auto", "break", "case", "char", "const", "continue", "default", "do",
    "double", "else", "enum", "extern", "float", "for", "goto", "if", "inline",
    "int", "long", "register", "restrict", "return", "short", "signed", "sizeof",
    "static", "struct", "switch", "typedef", "union", "unsigned", "void",
    "volatile", "while", "_Alignas", "_Alignof", "_Atomic", "_Bool", "_Complex",
    "_Generic", "_Imaginary", "_Noreturn", "_Static_assert", "_Thread_local",
}


def locate(language: str, source: str, file: str, line: int) -> LocatedFunction:
    lang = language.strip().lower()
    if lang in {"python", "py"}:
        functions = _python_functions(source)
    elif lang == "c":
        functions = _c_functions(source)
    else:
        raise ValueError(f"unsupported language: {language}")
    return _pick(functions, file, line, source)


def _pick(functions: list[LocatedFunction], file: str, line: int, source: str) -> LocatedFunction:
    if not functions:
        raise NoEnclosingFunction(file, line)
    containing = [fn for fn in functions if fn.start_line <= line <= fn.end_line]
    if not containing:
        raise LineOutsideFunction(file, line)
    if any(fn.nested for fn in containing):
        raise NestedDefinition(file, line)
    non_nested = [fn for fn in containing if not fn.nested]
    if len(non_nested) > 1:
        raise MultipleMatches(file, line)
    return non_nested[0]


def _python_functions(source: str) -> list[LocatedFunction]:
    tree = ast.parse(source)
    found: list[LocatedFunction] = []

    def walk(nodes, class_name: str | None, nested: bool) -> None:
        for node in nodes:
            if isinstance(node, ast.ClassDef):
                walk(node.body, node.name, nested)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                start = node.lineno
                if node.decorator_list:
                    start = min(dec.lineno for dec in node.decorator_list)
                found.append(LocatedFunction(
                    name=node.name,
                    start_line=start,
                    end_line=node.end_lineno or node.lineno,
                    nested=nested,
                    class_name=class_name,
                ))
                walk(node.body, class_name, True)
            elif isinstance(node, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.With,
                                   ast.AsyncWith, ast.Try, ast.ExceptHandler)):
                walk(node.body, class_name, nested)
                for name in ("orelse", "finalbody", "handlers"):
                    walk(getattr(node, name, []), class_name, nested)
            elif isinstance(node, ast.Match):
                for case in node.cases:
                    walk(case.body, class_name, nested)

    walk(tree.body, None, False)
    return found


def _c_functions(source: str) -> list[LocatedFunction]:
    code = _mask_c(source)
    functions: list[LocatedFunction] = []
    stack: list[tuple[int, int]] = []
    depth = 0
    i = 0
    n = len(code)
    while i < n:
        ch = code[i]
        if ch == "{":
            header = _c_function_header(code, i)
            if header is not None:
                name, start_line = header
                functions.append(LocatedFunction(
                    name=name,
                    start_line=start_line,
                    end_line=start_line,
                    nested=bool(stack),
                ))
                stack.append((len(functions) - 1, depth))
            depth += 1
            i += 1
            continue
        if ch == "}":
            depth -= 1
            if stack and stack[-1][1] == depth:
                idx, _ = stack.pop()
                functions[idx] = LocatedFunction(
                    name=functions[idx].name,
                    start_line=functions[idx].start_line,
                    end_line=_line_at(source, i),
                    nested=functions[idx].nested,
                    class_name=functions[idx].class_name,
                )
            i += 1
            continue
        i += 1
    return functions


def _c_function_header(code: str, brace: int) -> tuple[str, int] | None:
    j = _skip_space_back(code, brace - 1)
    if j is None or code[j] != ")":
        return None
    open_paren = _match_paren_backward(code, j)
    if open_paren is None:
        return None
    name_end = _skip_space_back(code, open_paren - 1)
    if name_end is None or not _is_ident_char(code[name_end]):
        return None
    name_start = name_end
    while name_start > 0 and _is_ident_char(code[name_start - 1]):
        name_start -= 1
    name = code[name_start:name_end + 1]
    if name in _C_KEYWORDS:
        return None
    sig_start = _signature_start(code, name_start)
    return name, _line_at(code, sig_start)


def _signature_start(code: str, name_start: int) -> int:
    i = name_start
    while True:
        prev = _skip_signature_space(code, i - 1)
        if prev is None:
            return i
        if code[prev] == "*":
            i = prev
            continue
        if _is_ident_char(code[prev]):
            start = prev
            while start > 0 and _is_ident_char(code[start - 1]):
                start -= 1
            i = start
            continue
        return i


def _skip_signature_space(code: str, i: int) -> int | None:
    """Skip spaces and one line continuation; stop at a blank line."""
    while i >= 0 and code[i] in " \t\r":
        i -= 1
    if i < 0:
        return None
    if code[i] != "\n":
        return i
    k = i - 1
    while k >= 0 and code[k] in " \t\r":
        k -= 1
    if k < 0 or code[k] == "\n":
        return None
    return k


def _skip_space_back(code: str, i: int) -> int | None:
    while i >= 0 and code[i].isspace():
        i -= 1
    return i if i >= 0 else None


def _match_paren_backward(code: str, close_i: int) -> int | None:
    depth = 0
    i = close_i
    while i >= 0:
        if code[i] == ")":
            depth += 1
        elif code[i] == "(":
            depth -= 1
            if depth == 0:
                return i
        i -= 1
    return None


def _is_ident_char(ch: str) -> bool:
    return ch.isalnum() or ch == "_"


def _line_at(source: str, index: int) -> int:
    return source.count("\n", 0, index) + 1


def _mask_c(source: str) -> str:
    out = []
    i = 0
    n = len(source)
    line_start = True
    while i < n:
        ch = source[i]
        if line_start and ch == "#":
            i = _mask_preprocessor(source, i, out)
            line_start = True
            continue
        if ch == "/" and i + 1 < n and source[i + 1] == "/":
            i = _mask_until(source, i, out, "\n", keep_last=True)
            line_start = True
            continue
        if ch == "/" and i + 1 < n and source[i + 1] == "*":
            i = _mask_block_comment(source, i, out)
            line_start = bool(out and out[-1] == "\n")
            continue
        if ch == '"':
            i = _mask_quote(source, i, out, '"')
            line_start = False
            continue
        if ch == "'":
            i = _mask_quote(source, i, out, "'")
            line_start = False
            continue
        out.append(ch)
        line_start = ch == "\n"
        i += 1
    return "".join(out)


def _mask_preprocessor(source: str, i: int, out: list[str]) -> int:
    n = len(source)
    while i < n:
        ch = source[i]
        if ch == "\n" and (i == 0 or source[i - 1] != "\\"):
            out.append("\n")
            return i + 1
        out.append("\n" if ch == "\n" else " ")
        i += 1
    return i


def _mask_until(source: str, i: int, out: list[str], stop: str, keep_last: bool) -> int:
    n = len(source)
    while i < n:
        ch = source[i]
        if ch == stop:
            if keep_last:
                out.append(ch)
                return i + 1
            out.append(" ")
            return i
        out.append("\n" if ch == "\n" else " ")
        i += 1
    return i


def _mask_block_comment(source: str, i: int, out: list[str]) -> int:
    n = len(source)
    out.extend("  ")
    i += 2
    while i < n:
        ch = source[i]
        if ch == "*" and i + 1 < n and source[i + 1] == "/":
            out.extend("  ")
            return i + 2
        out.append("\n" if ch == "\n" else " ")
        i += 1
    return i


def _mask_quote(source: str, i: int, out: list[str], quote: str) -> int:
    n = len(source)
    out.append(" ")
    i += 1
    while i < n:
        ch = source[i]
        if ch == "\\" and i + 1 < n:
            out.extend("  ")
            i += 2
            continue
        if ch == quote:
            out.append(" ")
            return i + 1
        out.append("\n" if ch == "\n" else " ")
        i += 1
    return i
