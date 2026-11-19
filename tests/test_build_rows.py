import json

import pytest

from training import build_rows


def row(cls="sql_injection", source="gold:test"):
    cwe = build_rows.CLASS_CWE[cls]
    language = build_rows.CLASS_LANGUAGE[cls]
    return {
        "finding": {
            "file": "example.py" if language == "python" else "example.c",
            "line": "2",
            "cwe": cwe.lower(),
            "severity": "warning",
            "rule_id": "test-rule",
            "language": "py" if language == "python" else language,
            "owasp": build_rows.CLASS_OWASP[cls],
        },
        "vulnerable_code": "def vulnerable(value): return value",
        "repair": "def vulnerable(value): return str(value)",
        "explanation": "Converts the value safely.",
        "source": source,
        "class": cls,
        "cwe": cwe.lower(),
    }


def test_normalize_row_canonicalizes_fields_and_values():
    result = build_rows.normalize_row(row())

    assert result["finding"]["line"] == 2
    assert result["finding"]["cwe"] == "CWE-89"
    assert result["finding"]["language"] == "python"
    assert result["finding"]["severity"] == "medium"
    assert tuple(result) == build_rows.ROW_FIELDS
    assert tuple(result["finding"]) == build_rows.FINDING_FIELDS


@pytest.mark.parametrize(
    ("cls", "cwe"),
    [("sql_injection", "CWE-79"), ("xss", "CWE-78"), ("buffer_overflow", "CWE-121")],
)
def test_class_cwe_mismatch_is_rejected(cls, cwe):
    value = row(cls)
    value["cwe"] = cwe
    value["finding"]["cwe"] = cwe

    with pytest.raises(ValueError, match="must use"):
        build_rows.normalize_row(value)


def test_missing_finding_field_is_rejected():
    value = row()
    del value["finding"]["rule_id"]

    with pytest.raises(ValueError, match="finding missing required fields"):
        build_rows.normalize_row(value)


def test_finding_cwe_must_match_outer_cwe():
    value = row()
    value["finding"]["cwe"] = "CWE-79"

    with pytest.raises(ValueError, match="requires finding CWE"):
        build_rows.normalize_row(value)


def test_exclusion_check_fails_on_exact_normalized_protected_match(monkeypatch):
    value = build_rows.normalize_row(row())
    normalized = build_rows.normalized_functions(value["vulnerable_code"], "python")
    monkeypatch.setattr(build_rows, "_protected_sources", lambda: [("corpus/dev/example.py", "python", normalized)])

    with pytest.raises(ValueError, match="exactly overlaps DEV/benchmark"):
        build_rows.check_exclusions([value])


def test_c_function_normalization_ignores_comments_but_keeps_string_literals():
    source = 'void show(const char *url) { /* note */ puts("http://example/a"); }'
    reference = 'void show ( const char* url ) { // note\n puts ( "http://example/a" ) ; }'

    assert build_rows.normalized_functions(source, "c") == build_rows.normalized_functions(reference, "c")


def test_build_dataset_writes_deterministic_rows_and_report(tmp_path, monkeypatch, capsys):
    gold_ids = sorted(build_rows.GOLD_CASE_IDS)
    gold_rows = [row("sql_injection", f"gold:corpus/train/{case_id}") for case_id in gold_ids]
    # Give each gold item unique code so this test focuses on construction, not overlap.
    for index, item in enumerate(gold_rows):
        item["vulnerable_code"] = f"def vulnerable_{index}(value): return value + {index}"
    python_path = tmp_path / "python.jsonl"
    c_path = tmp_path / "c.jsonl"
    gold_path = tmp_path / "gold.jsonl"
    rows_path = tmp_path / "rows.jsonl"
    report_path = tmp_path / "report.json"
    python_path.write_text(json.dumps(row("xss", "sven:test")) + "\n", encoding="utf-8")
    c_path.write_text(json.dumps(row("buffer_overflow", "juliet:test")) + "\n", encoding="utf-8")
    monkeypatch.setattr(build_rows, "check_exclusions", lambda rows: 3)

    report = build_rows.build_dataset(
        gold_rows=gold_rows,
        python_path=python_path,
        c_path=c_path,
        gold_path=gold_path,
        rows_path=rows_path,
        report_path=report_path,
    )

    output_rows = [json.loads(line) for line in rows_path.read_text(encoding="utf-8").splitlines()]
    assert len(output_rows) == 10
    assert report["gold_row_count"] == 8
    assert report["class_counts"] == {"buffer_overflow": 1, "sql_injection": 8, "xss": 1}
    assert report["source_counts"] == {"gold": 8, "juliet": 1, "sven": 1}
    assert report["exclusion_check"]["protected_source_count"] == 3
    assert json.loads(report_path.read_text(encoding="utf-8")) == report
    output = capsys.readouterr().out
    assert "Total rows: 10" in output
    assert "Rows per class:" in output
    assert "Rows per source:" in output

