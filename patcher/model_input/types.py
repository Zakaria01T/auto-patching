from dataclasses import dataclass, asdict


CLASS_BY_CWE = {
    "CWE-89": "sql_injection",
    "CWE-79": "xss",
    "CWE-78": "command_injection",
    "CWE-120": "buffer_overflow",
}


@dataclass(frozen=True)
class LocatedFunction:
    name: str
    start_line: int
    end_line: int
    nested: bool
    class_name: str | None = None


@dataclass(frozen=True)
class ModelInput:
    """Full function plus imports/context and finding metadata for the model."""

    language: str
    function_name: str
    function_source: str
    context: str
    class_name: str | None
    cwe: str
    rule_id: str
    vulnerability_class: str | None
    file: str
    line: int

    def as_dict(self) -> dict:
        return asdict(self)
