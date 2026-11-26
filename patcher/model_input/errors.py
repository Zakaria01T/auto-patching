"""Ambiguous-target errors. Messages always include file, line, and reason."""


class AmbiguousTarget(Exception):
    """Finding line cannot be mapped to exactly one non-nested function."""

    def __init__(self, file: str, line: int, reason: str):
        self.file = file
        self.line = line
        self.reason = reason
        super().__init__(f"{file}:{line}: {reason}")


class NoEnclosingFunction(AmbiguousTarget):
    def __init__(self, file: str, line: int):
        super().__init__(file, line, "the file has no functions")


class LineOutsideFunction(AmbiguousTarget):
    def __init__(self, file: str, line: int):
        super().__init__(
            file,
            line,
            "the line is in global code, between functions, in a class body "
            "but outside a method, or past the end of the file",
        )


class NestedDefinition(AmbiguousTarget):
    def __init__(self, file: str, line: int):
        super().__init__(
            file,
            line,
            "the line is inside a function defined inside another function",
        )


class MultipleMatches(AmbiguousTarget):
    def __init__(self, file: str, line: int):
        super().__init__(
            file,
            line,
            "two or more non-nested functions contain the line",
        )
