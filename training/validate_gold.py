"""Validate gold repairs: normal test, attack blocked, scanner (Python), ASan (C)."""
import importlib.util
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRAIN = ROOT / "corpus" / "train"
sys.path.insert(0, str(Path(__file__).resolve().parent))


def load(path):
    spec = importlib.util.spec_from_file_location("m", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@contextmanager
def workdir():
    old, d = os.getcwd(), tempfile.mkdtemp()
    os.chdir(d)
    try:
        yield
    finally:
        os.chdir(old)
        shutil.rmtree(d, ignore_errors=True)


def db():
    c = sqlite3.connect(":memory:")
    c.execute("CREATE TABLE invoices (id INTEGER, number TEXT, total REAL)")
    c.executemany("INSERT INTO invoices VALUES (?,?,?)", [(1, "A-100", 50.0), (2, "B-200", 75.0)])
    c.execute("CREATE TABLE teams (id INTEGER, name TEXT, owner TEXT)")
    c.execute("INSERT INTO teams VALUES (1, 'red', 'alice')")
    return c


# Each check returns (normal_ok, attack_blocked).
def sqli_01(m):
    return (m.find_invoice(db(), "A-100") == [(1, 50.0)],
            m.find_invoice(db(), "x' OR '1'='1") == [])


def sqli_02(m):
    c = db(); m.rename_team(c, 1, "blue")
    normal = c.execute("SELECT name, owner FROM teams").fetchall() == [("blue", "alice")]
    c = db(); m.rename_team(c, 1, "x', owner = 'evil")
    return normal, c.execute("SELECT owner FROM teams").fetchone()[0] == "alice"


def xss_01(m):
    return (m.welcome("Sara") == "<h1>Welcome Sara</h1>",
            "<script>" not in m.welcome("<script>alert(1)</script>"))


def xss_02(m):
    return (m.profile_link("https://example.com/sara", "Sara") == "<a href='https://example.com/sara'>Sara</a>",
            "javascript:" not in m.profile_link("javascript:alert(1)", "x"))


def cmdi_01(m):
    with workdir():
        os.mkdir("docs"); Path("docs/a.txt").write_text("x")
        normal = m.archive_folder("docs") == 0 and Path("out.tgz").exists()
        m.archive_folder("docs; touch pwned")
        return normal, not Path("pwned").exists()


def cmdi_02(m):
    with workdir():
        Path("notes.txt").write_text("a\nb\nc\n")
        normal = m.first_lines("notes.txt") == b"a\nb\n"
        try:
            m.first_lines("notes.txt; touch pwned")
        except Exception:
            pass
        return normal, not Path("pwned").exists()


PY = {"gold_sqli_01": sqli_01, "gold_sqli_02": sqli_02, "gold_xss_01": xss_01,
      "gold_xss_02": xss_02, "gold_cmdi_01": cmdi_01, "gold_cmdi_02": cmdi_02}
C = {"gold_bof_01": ("show_path", "a.txt", "/data/a.txt\n", "A" * 100),
     "gold_bof_02": ("greet_user", "Bob", "Hello Bob\n", "B" * 100)}


def c_check(src, func, normal_arg, expected, attack_arg):
    env = {**os.environ, "ASAN_OPTIONS": "detect_leaks=0"}
    with tempfile.TemporaryDirectory() as d:
        exe = str(Path(d) / "t")
        cmd = ["gcc", "-std=c11", "-g", "-fsanitize=address", f'-DSRC="{Path(src).as_posix()}"',
               f"-DFUNC={func}", str(ROOT / "training" / "harness.c"), "-o", exe]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode:
            print(r.stderr)
            return False, False
        n = subprocess.run([exe, normal_arg], capture_output=True, text=True, env=env)
        a = subprocess.run([exe, attack_arg], capture_output=True, text=True, env=env)
        return (n.returncode == 0 and n.stdout == expected,
                a.returncode == 0 and "AddressSanitizer" not in a.stderr)


def scanner_status(vuln, rep, lang, cwe):
    """Is the original finding (highest severity, same CWE) gone from the repair?"""
    try:
        from build_rows import scan_file, primary_finding
        orig = primary_finding(scan_file(vuln, lang), cwe)
        if orig is None:
            return "skipped (scanner did not report the CWE on the original)"
        after = scan_file(rep, lang)
        rules = {f["rule_id"] for f in after}
        others = sorted(rules - {orig["rule_id"]})
        if orig["rule_id"] in rules:
            return f"original rule still reported: {orig['rule_id']}"
        note = f" (other findings: {others})" if others else ""
        return f"original finding gone ({orig['rule_id']}){note}"
    except Exception as e:
        return f"skipped ({e})"


def main():
    failed = False
    for d in sorted(TRAIN.glob("gold_*")):
        meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
        lang, cid = meta["language"], meta["id"]
        ext = "py" if lang == "python" else "c"
        vuln, rep = d / f"vulnerable.{ext}", d / f"repair.{ext}"
        if lang == "python":
            normal, blocked = PY[cid](load(rep))
            v_normal, v_blocked = PY[cid](load(vuln))
        else:
            normal, blocked = c_check(rep, *C[cid])
            v_normal, v_blocked = c_check(vuln, *C[cid])
        scan = scanner_status(vuln, rep, lang, meta["cwe"])
        ok = normal and blocked and v_normal and not v_blocked
        if lang == "python":  # for C the scanner status is recorded only
            ok = ok and scan.startswith("original finding gone")
        failed |= not ok
        print(f"{'PASS' if ok else 'FAIL'}  {cid}: normal={normal} attack_blocked={blocked} "
              f"| attack_works_on_original={v_normal and not v_blocked} | scanner: {scan}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()