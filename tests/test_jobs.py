import pytest
from fastapi.testclient import TestClient

from api import main

client = TestClient(main.app)

@pytest.fixture(autouse=True)
def fake_scan(monkeypatch):
    """Every test uses a fake scan that finds nothing. CI has no scanner tools."""
    calls = []

    def _fake(path, language):
        calls.append((path, language))
        return []

    monkeypatch.setattr(main, "scan", _fake)
    return calls

def upload(name, content, tmp_path, monkeypatch):
    """Helper: point the API at a temp folder, then upload one file."""
    monkeypatch.setattr(main, "UPLOAD_DIR", tmp_path)
    return client.post("/jobs", files={"file": (name, content)})


def test_python_file_is_accepted(tmp_path, monkeypatch):
    r = upload("a.py", b"print(1)", tmp_path, monkeypatch)
    assert r.json()["language"] == "python"
    assert r.json()["status"] == main.UPLOADED


def test_c_file_is_accepted(tmp_path, monkeypatch):
    r = upload("a.c", b"int main(void){return 0;}", tmp_path, monkeypatch)
    assert r.json()["language"] == "c"
    assert r.json()["status"] == main.UPLOADED


def test_txt_file_is_rejected(tmp_path, monkeypatch):
    r = upload("notes.txt", b"hi", tmp_path, monkeypatch)
    assert r.json()["status"] == main.REJECTED
    assert r.json()["language"] is None


def test_too_large_file_is_rejected(tmp_path, monkeypatch):
    r = upload("big.py", b"x" * (main.MAX_BYTES + 1), tmp_path, monkeypatch)
    assert r.json()["status"] == main.REJECTED
    
def test_safe_python_file_ends_clean(tmp_path, monkeypatch, fake_scan):
    r = upload("a.py", b"print(1)", tmp_path, monkeypatch)
    job = client.get(f"/jobs/{r.json()['id']}").json()
    assert job["status"] == main.CLEAN
    assert job["findings"] == []
    path, language = fake_scan[0]
    assert path.endswith("original") 
    assert language == "python"

def test_txt_file_stays_rejected_and_is_not_scanned(tmp_path, monkeypatch, fake_scan):
    r = upload("notes.txt", b"hi", tmp_path, monkeypatch)
    job = client.get(f"/jobs/{r.json()['id']}").json()
    assert job["status"] == main.REJECTED
    assert job["findings"] is None
    assert fake_scan == []
    
def test_findings_are_stored(tmp_path, monkeypatch):
    finding = {
        "file": "a.py", "line": 3, "cwe": "CWE-89", "severity": "high",
        "rule_id": "x", "language": "python", "owasp": "A03:2021-Injection",
    }
    monkeypatch.setattr(main, "scan", lambda path, language: [finding])
    r = upload("a.py", b"print(1)", tmp_path, monkeypatch)
    job = client.get(f"/jobs/{r.json()['id']}").json()
    assert job["status"] == main.SCANNING           # not clean, not patching
    assert job["findings"] == [finding]
    
def test_scan_crash_does_not_break_the_api(tmp_path, monkeypatch):
    def boom(path, language):
        raise RuntimeError("tool missing")

    monkeypatch.setattr(main, "scan", boom)
    r = upload("a.py", b"print(1)", tmp_path, monkeypatch)
    assert r.status_code == 200
    job = client.get(f"/jobs/{r.json()['id']}").json()
    assert set(job.keys()) == set(main.CONTRACT_FIELDS)

def test_response_matches_contract(tmp_path, monkeypatch):
    r = upload("a.py", b"print(1)", tmp_path, monkeypatch)
    job = client.get(f"/jobs/{r.json()['id']}").json()

    assert set(job.keys()) == set(main.CONTRACT_FIELDS)
    assert job["status"] in main.STATUSES
    assert job["findings"] == []
    for field in ["diff", "explanation", "attempts", "decision"]:
        assert job[field] is None


def test_unknown_job_returns_404(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "UPLOAD_DIR", tmp_path)
    assert client.get("/jobs/hello").status_code == 404
    assert client.get(
        "/jobs/00000000-0000-4000-8000-000000000000"
    ).status_code == 404


def test_invalid_status_is_refused():
    with pytest.raises(ValueError):
        main.to_contract({"id": "x", "status": "done"})