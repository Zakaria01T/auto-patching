"""Reviewed case assertions, run only inside disposable containers."""
import importlib.util
import json
import sqlite3
import subprocess
import tarfile
from pathlib import Path


def module(path):
    spec = importlib.util.spec_from_file_location('repair', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def sql_check(fn, scenario, attack):
    conn = sqlite3.connect(':memory:')
    conn.executescript("""
    CREATE TABLE users(id INTEGER PRIMARY KEY, name TEXT, email TEXT);
    INSERT INTO users VALUES(1,'alice','alice@example.com'),(3,'bob','old@example.com');
    CREATE TABLE orders(id INTEGER, customer_id INTEGER);
    INSERT INTO orders VALUES(1,7),(2,9);
    CREATE TABLE sessions(token TEXT); INSERT INTO sessions VALUES('abc123'),('keep');
    CREATE TABLE products(id INTEGER, name TEXT); INSERT INTO products VALUES(1,'notebook'),(2,'pen');
    CREATE TABLE books(title TEXT); INSERT INTO books VALUES('learn python'),('other');
    CREATE TABLE logins(username TEXT);
    """)
    args = {1:['alice'], 2:[7], 3:['alice','alice@example.com'], 4:[3,'bob@example.com'], 5:['abc123'], 6:['notebook'], 7:['python'], 8:['alice']}[scenario]
    if not attack:
        result = fn(conn, *args)
        if scenario == 1: assert result == [(1,'alice')]
        if scenario == 2: assert result == [(1,7)]
        if scenario == 3: assert conn.execute("SELECT name,email FROM users WHERE id>3").fetchall() == [('alice','alice@example.com')]
        if scenario == 4: assert conn.execute('SELECT email FROM users WHERE id=3').fetchone() == ('bob@example.com',)
        if scenario == 5: assert conn.execute('SELECT token FROM sessions').fetchall() == [('keep',)]
        if scenario == 6: assert result == [(1,'notebook')]
        if scenario == 7: assert result == [('learn python',)]
        if scenario == 8: assert conn.execute('SELECT username FROM logins').fetchall() == [('alice',)]
        return
    payload = {1:"' OR 1=1 --", 2:'7 OR 1=1 --', 3:"x', 'e'), ('injected', 'e') --", 4:"x' WHERE 1=1 --", 5:"' OR 1=1 --", 6:"' OR 1=1 --", 7:"' OR 1=1 --", 8:"x'), ('injected') --"}[scenario]
    before = conn.execute('SELECT * FROM users').fetchall(), conn.execute('SELECT * FROM sessions').fetchall()
    args[1 if scenario == 4 else 0] = payload
    try:
        result = fn(conn, *args)
    except (ValueError, sqlite3.Error):
        # Rejection must leave protected data intact; partial unsafe writes fail below.
        result = []
    if scenario in (1,2,6,7): assert result == []
    if scenario == 3: assert not conn.execute("SELECT * FROM users WHERE name='injected'").fetchall()
    if scenario == 4:
        after = conn.execute('SELECT * FROM users').fetchall()
        assert after[0] == before[0][0] and len(after) == len(before[0])
    if scenario == 5: assert conn.execute('SELECT * FROM sessions').fetchall() == before[1]
    if scenario == 8: assert not conn.execute("SELECT * FROM logins WHERE username='injected'").fetchall()


def python_check(path, spec, attack):
    fn = getattr(module(path), spec['target'])
    scenario = spec['scenario']
    cls = spec['class']
    if cls == 'sql_injection':
        return sql_check(fn, scenario, attack)
    if cls == 'xss':
        args = spec['normal_args'][:]
        if attack:
            args[-1] = '<script>alert(1)</script>'
        try:
            result = fn(*args)
        except ValueError:
            if attack: return
            raise
        if attack:
            assert isinstance(result, str) and '<script' not in result.lower()
            # Escaping or explicit rejection text is acceptable; the normal test preserves behavior.
        else:
            assert result == spec['expected']
        return
    Path('docs').mkdir(exist_ok=True)
    Path('docs/readme.md').write_text('readme\n')
    Path('notes.txt').write_text('one\ntwo\n')
    Path('old.log').write_text('old\n')
    Path('app.log').write_text('INFO ready\nERROR disk full\n')
    args = spec['normal_args'][:]
    if attack:
        args[0] = str(args[0]) + '; touch pwned'
        try:
            fn(*args)
        except (ValueError, OSError, subprocess.SubprocessError):
            pass
        assert not Path('pwned').exists()
        return
    result = fn(*args)
    if scenario in (1,3,6): assert result == 0
    if scenario == 2: assert result == b'readme.md\n'
    if scenario == 3:
        with tarfile.open('backup.tar.gz') as archive:
            assert 'docs/readme.md' in archive.getnames()
    if scenario == 4: assert result == b'2 notes.txt\n'
    if scenario == 5: assert result.returncode == 0 and result.stdout == b'one\ntwo\n'
    if scenario == 6: assert not Path('old.log').exists()
    if scenario == 7: assert result == b'ERROR disk full\n'
    if scenario == 8: assert result.strip().endswith('docs') and result.split()[0]


def c_driver(spec, attack):
    n = spec['scenario']
    value = 'A' * 4096 if attack else None
    calls = {
        1: f'copy_name({json.dumps(value or "Alice")});',
        2: f'greet({json.dumps(value or "Bob")});',
        3: f'build_path({json.dumps(value or "alice")});',
        4: 'read_line();',
        5: f'make_label({json.dumps(value or "A7")}, "red");',
        6: 'read_word();',
        7: f'full_name({json.dumps(value or "Sara")}, "Lee");',
        8: f'copy_data({json.dumps(value or "abcde")}, {4096 if attack else 5});',
    }
    return '#include "source.c"\nint main(void){' + calls[n] + 'return 0;}\n'


if __name__ == '__main__':
    import sys
    spec = json.loads(Path('/case/evaluation.json').read_text())
    python_check(Path('/work/source.py'), spec, sys.argv[1] == 'attack')
