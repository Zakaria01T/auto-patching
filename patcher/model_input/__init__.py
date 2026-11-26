"""Model input builder: scanner finding + source file → one function for the LLM.

This is the first step of patching. `patcher.generate` already expects a
`vulnerable_function` string; this package is what extracts that string.

Ambiguity rules (lambdas are ignored; methods on a class are not nested):

Error                 Raised when
-------------------   ----------------------------------------------------------
NoEnclosingFunction   the file has no functions at all
LineOutsideFunction   the line is in global code, between functions, in a class
                      body but outside a method, or past the end of the file
NestedDefinition      the line is inside a function defined inside another
                      function
MultipleMatches       two or more non-nested functions contain the line
                      (for example, two one-liners on one line)

Every error message includes the file, the line, and the reason.
"""

from .builder import build_model_input
from .errors import (
    AmbiguousTarget,
    LineOutsideFunction,
    MultipleMatches,
    NestedDefinition,
    NoEnclosingFunction,
)
from .types import ModelInput

__all__ = [
    "AmbiguousTarget",
    "LineOutsideFunction",
    "ModelInput",
    "MultipleMatches",
    "NestedDefinition",
    "NoEnclosingFunction",
    "build_model_input",
]
