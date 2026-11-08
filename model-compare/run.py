#!/usr/bin/env python3
"""P6 shared prompted/fine-tuned repair evaluation CLI."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import tempfile
import time
import uuid

from evaluation import ROOT, digest, finalize, load_cases, reports, validate_patch
from inference import IdentityError, generate, identity


def stamp():
    return datetime.now(timezone.utc).isoformat()


def code_hashes():
    paths = list((ROOT / 'model-compare').glob('*.py')) + list((ROOT / 'model-compare/prompts').glob('*.txt')) + list((ROOT / 'scanner').glob('*.py')) + list((ROOT / 'scanner/rules').glob('*.yaml')) + [ROOT / 'model-compare/Dockerfile', ROOT / 'requirements-scanners.txt']
    return {str(p.relative_to(ROOT)): digest(p) for p in sorted(paths)}


def read_config(path):
    c = json.loads(path.read_text())
    required = {'models', 'prompt_version', 'generation_parameters', 'inference_timeout', 'check_timeout', 'image', 'memory', 'cpus', 'pids_limit', 'ollama_url', 'scanner_configuration'}
    if set(c) != required:
        raise ValueError(f'configuration fields must be exactly {sorted(required)}')
    if not c['models'] or len({m['type'] for m in c['models']}) != len(c['models']):
        raise ValueError('configure one entry per model type')
    for m in c['models']:
        if set(m) != {'type', 'tag', 'checkpoint'} or m['type'] not in ('prompted', 'fine-tuned') or not m['checkpoint']:
            raise ValueError('model needs type, actual tag and immutable checkpoint digest')
    if c['prompt_version'] != 'v1' or c['scanner_configuration'] != 'project-original-v1':
        raise ValueError('unsupported prompt/scanner configuration')
    if 'temperature' not in c['generation_parameters']:
        raise ValueError('temperature is required')
    if not c['image'].startswith('sha256:') or len(c['image']) != 71:
        raise ValueError('pin image by full local sha256 image ID')
    for key in ('inference_timeout', 'check_timeout', 'cpus', 'pids_limit'):
        if not isinstance(c[key], (int, float)) or c[key] <= 0:
            raise ValueError(f'{key} must be positive')
    return c


def docker_base(c):
    return ['docker', 'run', '--rm', '--network=none', '--sysctl=net.ipv4.ping_group_range=0 2147483647', '--read-only', '--cap-drop=ALL', '--security-opt=no-new-privileges', '--user=65534:65534', '--memory=' + c['memory'], '--cpus=' + str(c['cpus']), '--pids-limit=' + str(c['pids_limit']), '--tmpfs=/tmp:rw,noexec,nosuid,size=256m,mode=1777', '--tmpfs=/work:rw,exec,nosuid,size=64m,mode=1777', '-v', str(ROOT / 'model-compare/worker.py') + ':/repo/model-compare/worker.py:ro', '-v', str(ROOT / 'model-compare/case_checks.py') + ':/repo/model-compare/case_checks.py:ro', '-v', str(ROOT / 'scanner') + ':/repo/scanner:ro']


def preflight(c, include_models=True):
    proc = subprocess.run(['docker', 'image', 'inspect', c['image'], '--format', '{{.Id}}'], capture_output=True, text=True, timeout=20, check=True)
    if proc.stdout.strip() != c['image']:
        raise RuntimeError('container image identity mismatch')
    # Only trusted version commands; no generated code is run during preflight.
    script = "import json,subprocess; print(json.dumps({x:subprocess.check_output([x,'--version'],stderr=subprocess.STDOUT,text=True).strip() for x in ['python3','gcc','git','semgrep','bandit','flawfinder','cppcheck']}))"
    proc = subprocess.run(docker_base(c) + ['--entrypoint=python3', c['image'], '-c', script], capture_output=True, text=True, timeout=120, check=True)
    versions = json.loads(proc.stdout)
    return dict(tools=versions, models=[identity(c, m) for m in c['models']] if include_models else [])


def check(c, folder, mode):
    name = 'p6-' + uuid.uuid4().hex
    argv = docker_base(c) + ['--name=' + name, '-v', str(folder.resolve()) + ':/case:ro', c['image'], mode]
    try:
        proc = subprocess.run(argv, capture_output=True, text=True, timeout=c['check_timeout'])
        if proc.returncode:
            raise RuntimeError('container check failed: ' + proc.stderr + proc.stdout)
        payload = json.loads(proc.stdout)
        if 'infrastructure_error' in payload:
            raise RuntimeError(payload['infrastructure_error'])
        return payload
    except subprocess.TimeoutExpired:
        raise
    finally:
        # A timed-out docker client does not itself stop the container.
        subprocess.run(['docker', 'rm', '-f', name], capture_output=True, timeout=15)


def scanner_keys(payload, cwe):
    return {(f['cwe'], f['rule_id']) for f in payload['findings'] if f['cwe'] == cwe}


def evaluate(c, model, case, directory, run_id, split):
    start = time.monotonic()
    folder = directory / case['id']
    folder.mkdir()
    record = dict(run_id=run_id, dataset_split=split, case_id=case['id'], vulnerability_class=case['class'], model_type=model['type'], model_tag=model['tag'], checkpoint_identity=model['checkpoint'], prompt_version=c['prompt_version'], temperature=c['generation_parameters']['temperature'], generation_parameters=c['generation_parameters'], timestamp=stamp(), raw_output_path=None, patch_path=None, valid_output=False, git_apply=False, functional_test_pass=None, attack_blocked=None, scanner_cleared=None, failure_reasons=[], execution_status='completed')
    try:
        spec = json.loads(case['spec'].read_text())
        if spec['class'] != case['class'] or spec['test_sha256'] != digest(case['test']):
            raise RuntimeError('assertion specification does not match case/test.txt')
        # Every check uses a fresh container and filesystem, including baseline checks.
        baseline_function = check(c, case['source'].parent, 'functional')
        baseline_attack = check(c, case['source'].parent, 'attack')
        baseline_scanner = check(c, case['source'].parent, 'scanner')
        record['baseline'] = dict(functional=baseline_function, attack=baseline_attack, scanner=baseline_scanner)
        original_keys = scanner_keys(baseline_scanner, case['cwe'])
        if not baseline_function['passed'] or baseline_attack['passed'] or baseline_attack.get('reason') == 'compilation_failed' or not original_keys:
            raise RuntimeError('baseline calibration failed: expected normal pass, exploitable attack and original CWE finding')
        original = case['source'].read_text()
        prompt = (ROOT / 'model-compare/prompts' / (c['prompt_version'] + '.txt')).read_text().format(filename=case['source'].name, vulnerability=case['class'], target=spec['target'], source=original)
        (folder / 'prompt.txt').write_text(prompt)
        try:
            raw = generate(c, model, prompt)
        except IdentityError:
            raise
        except Exception as exc:
            record['execution_status'] = 'model_failure'
            record['failure_reasons'].append('model_inference_error')
            if isinstance(exc, TimeoutError) or isinstance(getattr(exc, 'reason', None), TimeoutError):
                record['failure_reasons'].append('timeout')
            record['error'] = str(exc)
            return finalize(record)
        (folder / 'raw.txt').write_text(raw)
        record['raw_output_path'] = str((folder / 'raw.txt').relative_to(directory.parent))
        with tempfile.TemporaryDirectory(prefix='p6-patch-') as tmp:
            work = Path(tmp)
            validation = validate_patch(raw, original, case['source'].name, case['language'], spec['target'], work)
            patch = validation.pop('patch', '')
            (folder / 'repair.diff').write_text(patch)
            record['patch_path'] = str((folder / 'repair.diff').relative_to(directory.parent))
            record.update(validation)
            if not record['valid_output']:
                record['execution_status'] = 'model_failure'
                return finalize(record)
            for source, name in ((case['test'], 'test.txt'), (case['spec'], 'evaluation.json')):
                (work / name).write_bytes(source.read_bytes())
            (work / 'meta.json').write_text(json.dumps({k:case[k] for k in ('id','language','class','cwe')}))
            # TemporaryDirectory is private by default; container UID needs read/traverse access.
            work.chmod(0o755)
            for path in work.iterdir():
                if path.is_file(): path.chmod(0o644)
            for mode, metric in (('functional','functional_test_pass'), ('attack','attack_blocked'), ('scanner','scanner_cleared')):
                try:
                    payload = check(c, work, mode)
                except subprocess.TimeoutExpired:
                    if mode == 'scanner': raise
                    record[metric] = False
                    record['failure_reasons'].append('timeout')
                    continue
                record[mode + '_evidence'] = payload
                if mode == 'scanner':
                    record[metric] = not (original_keys & scanner_keys(payload, case['cwe']))
                    if not record[metric]: record['failure_reasons'].append('scanner_finding_persisted')
                else:
                    record[metric] = payload['passed']
                    if not payload['passed']: record['failure_reasons'].append(payload['reason'])
    except Exception as exc:
        record['execution_status'] = 'infrastructure_error'
        record['failure_reasons'].append('infrastructure_error')
        if isinstance(exc, subprocess.TimeoutExpired): record['failure_reasons'].append('timeout')
        record['error'] = str(exc)
    finally:
        record['duration_seconds'] = time.monotonic() - start
    if record['execution_status'] == 'completed' and not all(record.get(k) is True for k in ('valid_output', 'functional_test_pass', 'attack_blocked')):
        record['execution_status'] = 'model_failure'
    return finalize(record)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['check-dev','calibrate-dev','freeze','run'])
    parser.add_argument('--config', type=Path)
    parser.add_argument('--case', action='append', dest='case_ids', help='DEV calibration only; repeat for multiple cases')
    parser.add_argument('--frozen', type=Path)
    parser.add_argument('--dataset', choices=['dev','benchmark'], default='dev')
    parser.add_argument('--authorize-final', action='store_true')
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'model-compare/results')
    args = parser.parse_args()
    if args.dataset == 'benchmark' and (not args.authorize_final or not args.frozen or args.action != 'run'):
        parser.error('FINAL requires run --authorize-final --frozen PATH')
    if args.case_ids and args.action != 'calibrate-dev':
        parser.error('--case is only supported for DEV calibration')
    if args.action == 'check-dev':
        cases = load_cases('dev')
        for case in cases:
            spec = json.loads(case['spec'].read_text())
            if spec['test_sha256'] != digest(case['test']): raise ValueError('test specification drift')
        print(f'DEV: validated {len(cases)} case manifests; no generated code executed')
        return
    if args.config is None: parser.error('--config required')
    c = read_config(args.config)
    hashes = code_hashes()
    if args.action == 'calibrate-dev':
        cases = load_cases('dev')
        if args.case_ids:
            if set(args.case_ids) - {case['id'] for case in cases}:
                parser.error('unknown DEV case ID')
            cases = [case for case in cases if case['id'] in args.case_ids]
        metadata = preflight(c, include_models=False)
        directory = args.output_dir.resolve() / 'dev' / ('calibration-' + uuid.uuid4().hex)
        directory.mkdir(parents=True, exist_ok=False)
        results = []
        for case in cases:
            item = dict(case_id=case['id'], dataset_split='dev')
            try:
                spec = json.loads(case['spec'].read_text())
                if spec['test_sha256'] != digest(case['test']):
                    raise RuntimeError('test specification drift')
                item['functional'] = check(c, case['source'].parent, 'functional')
                item['attack'] = check(c, case['source'].parent, 'attack')
                item['scanner'] = check(c, case['source'].parent, 'scanner')
                item['calibrated'] = bool(item['functional']['passed'] and not item['attack']['passed'] and item['attack'].get('reason') != 'compilation_failed' and scanner_keys(item['scanner'], case['cwe']))
            except Exception as exc:
                item.update(calibrated=False, infrastructure_error=str(exc))
            results.append(item)
            print(case['id'], 'PASS' if item['calibrated'] else 'INCOMPLETE', flush=True)
        (directory / 'calibration.json').write_text(json.dumps(dict(environment=metadata, config=c, code_hashes=hashes, results=results), indent=2))
        print(directory)
        if not all(item['calibrated'] for item in results): raise SystemExit(2)
        return
    if args.action == 'freeze':
        if not args.frozen: parser.error('--frozen output path required')
        metadata = preflight(c)
        with args.frozen.open('x') as stream:
            json.dump(dict(config=c, code_hashes=hashes, environment=metadata, frozen_at=stamp()), stream, indent=2)
        print('Frozen configuration written to', args.frozen)
        return
    frozen = json.loads(args.frozen.read_text()) if args.frozen else None
    if frozen and (frozen['config'] != c or frozen['code_hashes'] != hashes):
        raise ValueError('frozen configuration or evaluator changed; freeze again before final authorization')
    cases = load_cases(args.dataset, args.authorize_final)
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S') + '-' + uuid.uuid4().hex[:12]
    directory = args.output_dir.resolve() / args.dataset / run_id
    directory.mkdir(parents=True, exist_ok=False)
    manifest = dict(run_id=run_id, dataset_split=args.dataset, config=c, code_hashes=hashes, timestamp=stamp(), repository_commit=subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip(), repository_dirty=bool(subprocess.check_output(['git','status','--porcelain'], cwd=ROOT, text=True)), frozen_sha256=digest(args.frozen) if args.frozen else None, cases={case['id']:{p.name:digest(p) for p in (case['source'],case['test'],case['spec'],case['source'].parent/'meta.json')} for case in cases})
    infrastructure_error = None
    try:
        manifest['environment'] = preflight(c)
        if frozen and manifest['environment'] != frozen['environment']:
            raise RuntimeError('frozen tool/model environment changed')
    except Exception as exc:
        infrastructure_error = str(exc)
        manifest['infrastructure_error'] = infrastructure_error
    (directory / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    records = []
    for model in c['models']:
        model_dir = directory / model['type']
        model_dir.mkdir()
        for case in cases:
            if infrastructure_error:
                record = finalize(dict(run_id=run_id, dataset_split=args.dataset, case_id=case['id'], vulnerability_class=case['class'], model_type=model['type'], model_tag=model['tag'], checkpoint_identity=model['checkpoint'], prompt_version=c['prompt_version'], temperature=c['generation_parameters']['temperature'], generation_parameters=c['generation_parameters'], timestamp=stamp(), raw_output_path=None, patch_path=None, valid_output=False, git_apply=False, functional_test_pass=None, attack_blocked=None, scanner_cleared=None, execution_status='infrastructure_error', failure_reasons=['infrastructure_error'], error=infrastructure_error, duration_seconds=0))
            else:
                record = evaluate(c, model, case, model_dir, run_id, args.dataset)
            records.append(record)
            # Append evidence after every case for interruption recovery.
            with (directory / 'journal.jsonl').open('a') as stream: stream.write(json.dumps(record) + '\n')
    reports(records, directory)
    print(directory)
    if any(r['execution_status'] == 'infrastructure_error' for r in records):
        raise SystemExit(2)


if __name__ == '__main__':
    main()
