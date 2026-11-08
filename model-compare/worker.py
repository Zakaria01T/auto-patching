"""Container entrypoint for independent functional, attack and scanner checks."""
import csv
import importlib
import io
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from case_checks import c_driver


def run_check(mode):
    os.chdir('/work')
    spec = json.loads(Path('/case/evaluation.json').read_text())
    meta = json.loads(Path('/case/meta.json').read_text())
    source = next(Path('/case').glob('source.*'))
    shutil.copy(source, Path('/work') / source.name)
    if mode == 'scanner':
        sys.path.insert(0, '/repo')
        scanner = importlib.import_module('scanner.scan')
        original_run = scanner._run
        def strict_run(argv):
            proc = original_run(argv)
            tool = Path(argv[0]).name
            allowed = (0, 1) if tool in ('bandit', 'semgrep') else (0,)
            if proc.returncode not in allowed:
                raise RuntimeError(f'{tool} exited {proc.returncode}: {proc.stderr}')
            if tool in ('semgrep', 'bandit'):
                payload = json.loads(proc.stdout)
                if not isinstance(payload.get('results'), list) or not isinstance(payload.get('errors'), list):
                    raise RuntimeError(f'{tool} returned an incomplete scanner payload')
                if payload.get('errors'):
                    raise RuntimeError(str(payload['errors']))
            if tool == 'flawfinder':
                fields = csv.DictReader(io.StringIO(proc.stdout)).fieldnames or []
                if not {'Line', 'CWEs', 'Level'}.issubset(fields):
                    raise RuntimeError('flawfinder returned an incomplete CSV payload')
            return proc
        scanner._run = strict_run
        findings = scanner.scan('/work/' + source.name, meta['language'])
        print(json.dumps({'findings': findings}))
        return 0
    if meta['language'] == 'python':
        proc = subprocess.run([sys.executable, '/repo/model-compare/case_checks.py', mode], capture_output=True, text=True)
    else:
        Path('driver.c').write_text(c_driver(spec, mode == 'attack'))
        compile_result = subprocess.run(['gcc', '-no-pie', '-fsanitize=address', '-fno-omit-frame-pointer', '-g', 'driver.c', '-o', '/work/check'], capture_output=True, text=True)
        if compile_result.returncode:
            print(json.dumps({'passed': False, 'reason': 'compilation_failed', 'log': compile_result.stderr}))
            return 0
        data = 'A' * 4096 if mode == 'attack' else spec['stdin']
        proc = subprocess.run(['/work/check'], input=data, capture_output=True, text=True, env=dict(os.environ, ASAN_OPTIONS='detect_leaks=0:abort_on_error=1'))
    sanitizer = 'AddressSanitizer' in proc.stderr or 'LeakSanitizer' in proc.stderr
    passed = proc.returncode == 0 and not sanitizer
    if meta['language'] == 'c' and mode == 'attack':
        passed = proc.returncode >= 0 and not sanitizer
    if meta['language'] == 'c' and mode == 'functional':
        passed = passed and proc.stdout == spec['expected']
    print(json.dumps({'passed': passed, 'reason': 'sanitizer_error' if sanitizer else ('functional_test_failed' if mode == 'functional' else 'attack_not_blocked'), 'log': (proc.stdout + proc.stderr)[-16000:]}))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(run_check(sys.argv[1]))
    except Exception as exc:
        print(json.dumps({'infrastructure_error': str(exc)}))
        sys.exit(2)
