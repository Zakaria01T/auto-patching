"""M2 patch service: call the model, parse its reply, reject bad replies.

Reply layout (prompt p5-v1):
    ```<language>
    <one complete corrected function>
    ```
    EXPLANATION: <one sentence>
    INCLUDES: <stdio.h>, <string.h>      (optional, C only)
Insertion into the file and the diff are other tasks; this module stops at a validated function.
"""
from dataclasses import dataclass
import re
import socket
from urllib.error import URLError

from .generate import generate as call_model
from .prompts import PROMPT_VERSION

_FENCE = re.compile(r"```([^\n`]*)\n(.*?)```", re.S)
_EXPLANATION = re.compile(r"^[ \t]*EXPLANATION:[ \t]*(.*\S)[ \t]*$", re.I | re.M)
_INCLUDES = re.compile(r"^[ \t]*INCLUDES:[ \t]*(.*)$", re.I | re.M)
_HEADER = re.compile(r"<[\w./]+>")
_C_INCLUDE = re.compile(r"^[ \t]*#[ \t]*include", re.M)
_LABELS = {"python": {"python", "py"}, "c": {"c"}}


class PatchError(Exception):
    """Base error. raw_answer is the model's reply (None if there was none), for the attempt log."""

    def __init__(self, message, raw_answer=None):
        super().__init__(message)
        self.raw_answer = raw_answer


class ModelTimeoutError(PatchError):
    """The model did not answer in time."""


class EmptyReplyError(PatchError):
    """The reply, or the code block in it, is empty."""


class MalformedReplyError(PatchError):
    """The reply does not follow the p5-v1 layout."""


class UnchangedFunctionError(PatchError):
    """The model returned the vulnerable function as it was."""


@dataclass(frozen=True)
class PatchResult:
    corrected_function: str
    explanation: str
    includes: tuple          # C headers from the INCLUDES line, empty for Python
    raw_answer: str          # untouched model reply, for the attempt log
    prompt_version: str = PROMPT_VERSION


def _normalize(code):
    """Line endings and trailing spaces do not count as a change."""
    return "\n".join(line.rstrip() for line in code.replace("\r\n", "\n").split("\n")).strip()


def _is_timeout(exc):
    timeouts = (TimeoutError, socket.timeout)
    return isinstance(exc, timeouts) or (isinstance(exc, URLError) and isinstance(exc.reason, timeouts))


def parse_reply(raw, original_function, language):
    """Return a PatchResult or raise a PatchError that carries the raw reply."""
    if raw is None or not raw.strip():
        raise EmptyReplyError("the model returned an empty reply", raw)

    fences = list(_FENCE.finditer(raw))
    if not fences:
        raise MalformedReplyError("no fenced code block in the reply", raw)
    if len(fences) > 1:
        raise MalformedReplyError(f"expected one code block, found {len(fences)}", raw)
    fence = fences[0]

    label = fence.group(1).strip().lower()
    if label and label not in _LABELS[language]:
        raise MalformedReplyError(f"code block is labelled {label!r}, expected {language}", raw)
    code = fence.group(2).strip("\n")
    if not code.strip():
        raise EmptyReplyError("the code block is empty", raw)
    if language == "c" and _C_INCLUDE.search(code):
        raise MalformedReplyError("#include inside the code block; headers belong on the INCLUDES line", raw)

    tail = raw[fence.end():]
    explanation = _EXPLANATION.search(tail)
    if not explanation:
        raise MalformedReplyError("missing EXPLANATION line after the code block", raw)

    if _normalize(code) == _normalize(original_function):
        raise UnchangedFunctionError("the model returned the function unchanged", raw)

    includes = ()
    if language == "c":
        line = _INCLUDES.search(tail)
        includes = tuple(_HEADER.findall(line.group(1))) if line else ()
    return PatchResult(code, explanation.group(1), includes, raw)


def generate_patch(finding, vulnerable_function, expected_behavior, db_driver=None, example=None,
                   **model_options):
    """Call patcher.generate.generate, then validate the reply.

    model_options go straight to generate (base_url, timeout, log_path, config_path, ...).
    """
    try:
        raw = call_model(finding, vulnerable_function, expected_behavior, db_driver, example,
                         **model_options)
    except Exception as exc:
        if _is_timeout(exc):
            raise ModelTimeoutError("the model did not answer in time") from exc
        raise
    return parse_reply(raw, vulnerable_function, finding["language"])