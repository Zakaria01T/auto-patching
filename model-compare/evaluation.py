"""Shared P6 evaluation primitives. No generated code is executed on the host."""
import ast
import csv
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLASSES = ('sql_injection', 'xss', 'command_injection', 'buffer_overflow')
METRICS = ('valid_output', 'functional_test_pass', 'attack_blocked', 'scanner_cleared', 'fix_success')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_cases(split, authorize_final=False):
    if split not in ('dev', 'benchmark'):
        raise ValueError('dataset must be dev or benchmark')
    if split == 'benchmark' and not authorize_final:
        raise ValueError('sealed benchmark requires --authorize-final and frozen configuration')
    base = ROOT / ('corpus/dev' if split == 'dev' else 'benchmark')
    if base.is_symlink() or base.resolve() != base.absolute():
        raise ValueError('dataset root must not be a symlink')
    for folder in base.iterdir():
        if folder.is_dir() and not folder.name.startswith(('_', '.')) and not (split == 'dev' and folder.name == 'samples') and not (folder / 'meta.json').is_file():
            raise ValueError(f'missing case metadata: {folder}')
    cases = []
    for meta_path in sorted(base.glob('*/meta.json')):
        if meta_path.parent.name.startswith('_'):
            continue
        if meta_path.is_symlink() or not meta_path.resolve().is_relative_to(base.resolve()):
            raise ValueError('case metadata must remain inside the selected dataset')
        meta = json.loads(meta_path.read_text())
        if meta['id'] != meta_path.parent.name or meta['class'] not in CLASSES:
            raise ValueError(f'invalid case metadata: {meta_path}')
        sources = list(meta_path.parent.glob('source.*'))
        if len(sources) != 1 or sources[0].suffix not in ('.py', '.c'):
            raise ValueError(f'one Python/C source required: {meta_path}')
        test = meta_path.parent / 'test.txt'
        spec = meta_path.parent / 'evaluation.json'
        if not test.is_file() or not spec.is_file():
            raise ValueError(f'missing test.txt or reviewed evaluation.json: {meta_path.parent}')
        if any(p.is_symlink() or not p.resolve().is_relative_to(base.resolve()) for p in (meta_path, sources[0], test, spec)):
            raise ValueError('case files must remain inside the selected dataset')
        if meta['language'] != ('python' if sources[0].suffix == '.py' else 'c'):
            raise ValueError('source language disagrees with metadata')
        case = dict(meta, source=sources[0], test=test, spec=spec)
        cases.append(case)
    if not cases or (split == 'dev' and len(cases) != 32):
        raise ValueError('dataset empty or DEV does not contain exactly 32 cases')
    return cases


def target_body(source, language, target):
    if language == 'python':
        nodes = [n for n in ast.parse(source).body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == target]
        if len(nodes) != 1:
            raise ValueError('target function missing or duplicated')
        return ast.dump(nodes[0], include_attributes=False)
    # Tokenize comments and literals before counting top-level function braces.
    tokens = re.findall(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|/\*.*?\*/|//[^\n]*|[A-Za-z_]\w*|\d+|[^\s]', source, re.S)
    tokens = [t for t in tokens if not t.startswith(('/*', '//'))]
    bodies, depth = [], 0
    for i, token in enumerate(tokens):
        if depth == 0 and token == target and tokens[i + 1:i + 2] == ['(']:
            end, parens = i + 2, 1
            while end < len(tokens) and parens:
                parens += (tokens[end] == '(') - (tokens[end] == ')')
                end += 1
            if tokens[end:end + 1] == ['{']:
                close, braces = end + 1, 1
                while close < len(tokens) and braces:
                    braces += (tokens[close] == '{') - (tokens[close] == '}')
                    close += 1
                if braces:
                    raise ValueError('unbalanced target function')
                bodies.append(tokens[i:close])
        depth += (token == '{') - (token == '}')
    if len(bodies) != 1:
        raise ValueError('target function missing or duplicated')
    return bodies[0]


def validate_patch(raw, original, name, language, target, work):
    """Accept one unified diff, constrain paths, apply with git, require target change."""
    result = dict(valid_output=False, git_apply=False, failure_reasons=[])
    def fail(reason):
        result['failure_reasons'].append(reason)
        return result
    if not raw.strip():
        return fail('empty_output')
    blocks = re.findall(r'```(?:diff|patch)?\s*\n(.*?)```', raw, re.S)
    patch = blocks[0] if len(blocks) == 1 else raw
    result['patch'] = patch
    if not patch.strip():
        return fail('empty_output')
    if patch.strip() == original.strip():
        return fail('no_change')
    headers = re.findall(r'^(---|\+\+\+) ([^\n\t]+)', patch, re.M)
    if headers != [('---', 'a/' + name), ('+++', 'b/' + name)] or '@@ ' not in patch:
        return fail('malformed_patch')
    work.mkdir(parents=True, exist_ok=True)
    path = work / name
    path.write_text(original)
    patch_path = work / 'repair.diff'
    patch_path.write_text(patch)
    subprocess.run(['git', 'init', '-q', str(work)], check=True, capture_output=True)
    stat = subprocess.run(['git', 'apply', '--numstat', '--', 'repair.diff'], cwd=work, capture_output=True, text=True, timeout=10)
    if stat.returncode == 0 and (len(stat.stdout.splitlines()) != 1 or stat.stdout.rstrip().split('\t')[-1] != name):
        return fail('wrong_target')
    proc = subprocess.run(['git', 'apply', '--verbose', '--', 'repair.diff'], cwd=work, capture_output=True, text=True, timeout=10)
    result['git_apply_log'] = proc.stdout + proc.stderr
    result['git_apply'] = proc.returncode == 0
    if proc.returncode:
        return fail('git_apply_failed')
    if path.is_symlink() or not path.is_file():
        return fail('wrong_target')
    changed = path.read_text()
    if changed == original:
        return fail('no_change')
    try:
        if target_body(original, language, target) == target_body(changed, language, target):
            return fail('wrong_target')
    except (ValueError, SyntaxError):
        return fail('wrong_target')
    result['valid_output'] = True
    return result


def finalize(record):
    record['failure_reasons'] = list(dict.fromkeys(record.get('failure_reasons', [])))
    record['fix_success'] = all(record.get(k) is True for k in METRICS[:3])
    record['skipped_checks'] = [k for k in METRICS[1:4] if record.get(k) is None]
    return record


def aggregate(records):
    if len({r['dataset_split'] for r in records}) != 1:
        raise ValueError('DEV and FINAL BENCHMARK cannot be mixed')
    rows = []
    for model in sorted({r['model_type'] + ':' + r['model_tag'] for r in records}):
        selected = [r for r in records if r['model_type'] + ':' + r['model_tag'] == model]
        for cls in (*CLASSES, 'OVERALL'):
            group = [r for r in selected if cls == 'OVERALL' or r['vulnerability_class'] == cls]
            complete = all(r['execution_status'] != 'infrastructure_error' for r in records)
            row = dict(model=model, dataset_split=records[0]['dataset_split'], vulnerability_class=cls, total=len(group), publishable=complete)
            for metric in METRICS:
                n = sum(r.get(metric) is True for r in group)
                row[metric + '_numerator'] = n
                row[metric + '_denominator'] = len(group)
                row[metric + '_percent'] = 100 * n / len(group) if group and complete else None
                row[metric + '_skipped'] = sum(r.get(metric) is None for r in group)
            rows.append(row)
    return rows


def reports(records, directory):
    rows = aggregate(records)
    (directory / 'records.jsonl').write_text(''.join(json.dumps(r, sort_keys=True) + '\n' for r in records))
    (directory / 'summary.json').write_text(json.dumps(rows, indent=2))
    with (directory / 'summary.csv').open('w') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    title = 'DEV' if records[0]['dataset_split'] == 'dev' else 'FINAL BENCHMARK'
    lines = [f'# {title} repair evaluation', '', 'Percentages are suppressed when infrastructure is incomplete. Counts retain all assigned cases.', '', '| Model | Class | Total | Valid % | Functional % | Attack % | Scanner % | Fix % |', '|---|---|---|---|---|---|---|---|']
    for row in rows:
        cells = [row['model'], row['vulnerability_class'], str(row['total'])]
        for metric in METRICS:
            pct = row[metric + '_percent']
            cells.append(f"{pct:.2f} ({row[metric + '_numerator']}/{row['total']})" if pct is not None else f"INCOMPLETE ({row[metric + '_numerator']}/{row['total']})")
        lines.append('| ' + ' | '.join(cells) + ' |')
    reasons = {}
    for r in records:
        for reason in r['failure_reasons']:
            reasons[reason] = reasons.get(reason, 0) + 1
    lines += ['', 'Failure reasons (multiple per case):', '', json.dumps(reasons, indent=2), '', 'See manifest.json for frozen conditions and records.jsonl for skipped checks, durations and evidence.']
    (directory / 'report.md').write_text('\n'.join(lines) + '\n')
