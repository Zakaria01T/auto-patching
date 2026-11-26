"""Build model input from a scanner finding and uploaded source."""

from .context import gather, slice_function
from .locator import locate
from .types import CLASS_BY_CWE, ModelInput

_FINDING_FIELDS = ("file", "line", "cwe", "severity", "rule_id", "language", "owasp")


def build_model_input(finding: dict, source: str) -> ModelInput:
    """Return the full vulnerable function, needed context, and finding metadata."""
    _require_finding(finding)
    if not isinstance(source, str):
        raise TypeError("source must be a string")
    language = finding["language"]
    file = finding["file"]
    line = int(finding["line"])
    located = locate(language, source, file, line)
    return ModelInput(
        language="c" if language.strip().lower() == "c" else "python",
        function_name=located.name,
        function_source=slice_function(source, located),
        context=gather(language, source, located),
        class_name=located.class_name,
        cwe=finding["cwe"],
        rule_id=finding["rule_id"],
        vulnerability_class=CLASS_BY_CWE.get(finding["cwe"]),
        file=file,
        line=line,
    )


def _require_finding(finding: dict) -> None:
    if not isinstance(finding, dict):
        raise TypeError("finding must be a dict")
    missing = [name for name in _FINDING_FIELDS if name not in finding]
    if missing:
        raise ValueError(f"finding missing fields: {', '.join(missing)}")
