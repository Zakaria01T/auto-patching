"""Collect imports, includes, and enclosing-class context for a located function."""

import ast

from .types import LocatedFunction


def gather(language: str, source: str, located: LocatedFunction) -> str:
    lang = language.strip().lower()
    if lang in {"python", "py"}:
        return _python_context(source, located)
    if lang == "c":
        return _c_context(source)
    raise ValueError(f"unsupported language: {language}")


def slice_function(source: str, located: LocatedFunction) -> str:
    lines = source.splitlines(keepends=True)
    return "".join(lines[located.start_line - 1:located.end_line])


def _python_context(source: str, located: LocatedFunction) -> str:
    tree = ast.parse(source)
    parts: list[str] = []
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            chunk = ast.get_source_segment(source, node)
            if chunk:
                parts.append(chunk)
    if located.class_name:
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name == located.class_name:
                bases = ", ".join(ast.get_source_segment(source, b) or "" for b in node.bases)
                header = f"class {node.name}({bases}):" if bases else f"class {node.name}:"
                parts.append(header)
                break
    return "\n".join(parts)


def _c_context(source: str) -> str:
    includes = []
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith("#include"):
            includes.append(stripped)
    return "\n".join(includes)
