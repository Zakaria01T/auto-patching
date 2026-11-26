#!/usr/bin/env python3
"""P6 shared prompted/fine-tuned repair evaluation CLI."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import tempfile
import time
import uuid
import hashlib

from evaluation import ROOT, digest, finalize, load_cases, reports, validate_patch
from inference import IdentityError, generate, identity
from p5_eval import ReplayInputError, build_case_prompts, function_response_to_diff


def stamp():
    return datetime.now(timezone.utc).isoformat()


def code_hashes():
    paths = list((ROOT / 'model-compare').glob('*.py')) + list((ROOT / 'model-compare/prompts').glob('*.txt')) + list((ROOT / 'scanner').glob('*.py')) + list((ROOT / 'scanner/rules').glob('*.yaml')) + [ROOT / 'model-compare/Dockerfile', ROOT / 'requirements-scanners.txt', ROOT / 'patcher/prompts.py']
    paths += [ROOT / 'model-compare/docs/evaluation-methodology.md', ROOT / 'model-compare/docs/p5-offline-replay.md']
    return {str(p.relative_to(ROOT)): digest(p) for p in sorted(paths)}


def read_config(path, calibration_only=False):
    c = json.loads(path.read_text())
    required = {'models', 'prompt_version', 'generation_parameters', 'inference_timeout', 'check_timeout', 'image', 'memory', 'cpus', 'pids_limit', 'ollama_url', 'scanner_configuration'}
    optional = {'inference_backend', 'replay_metadata', 'calibration_only', 'legacy_manifest'}
    if not required <= set(c) or set(c) - required - optional:
        raise ValueError(f'configuration fields must be exactly {sorted(required)}')
    c.setdefault('inference_backend', 'ollama')
    if 'legacy_manifest' in c and type(c['legacy_manifest']) is not bool:
        raise ValueError('legacy_manifest must be a boolean')
    if c.get('legacy_manifest', False) and c['inference_backend'] != 'replay':
        raise ValueError('legacy_manifest is permitted only for offline replay')
    if c.get('calibration_only', False) is not calibration_only:
        raise ValueError('calibration_only config is valid only for calibrate-dev')
    if c['inference_backend'] not in ('ollama', 'replay'):
        raise ValueError('inference_backend must be ollama or replay')
    if not c['models'] or len({m.get('tag') for m in c['models']}) != len(c['models']):
        raise ValueError('configure one entry per unique model tag')
    for m in c['models']:
        allowed_model_fields = (
            {'type', 'tag', 'checkpoint'},
            {'type', 'tag', 'checkpoint', 'adapter_sha256'},
            {'type', 'tag', 'checkpoint', 'training_settings_provenance'},
            {'type', 'tag', 'checkpoint', 'adapter_sha256', 'training_settings_provenance'},
        )
        if set(m) not in allowed_model_fields or m['type'] not in ('prompted', 'fine-tuned') or not m['checkpoint']:
            raise ValueError('model needs type, tag and immutable checkpoint identity')
        if 'training_settings_provenance' in m and not isinstance(m['training_settings_provenance'], str):
            raise ValueError('training_settings_provenance must be a string')
        if m.get('adapter_sha256') is not None and not re.fullmatch(r'[0-9a-f]{64}', m['adapter_sha256']):
            raise ValueError('adapter_sha256 must be a lowercase SHA-256 digest')
    if c['prompt_version'] not in ('v1', 'p5-v1') or c['scanner_configuration'] != 'project-original-v1':
        raise ValueError('unsupported prompt/scanner configuration')
    if c['prompt_version'] == 'p5-v1':
        if c['inference_backend'] != 'replay' or 'replay_metadata' not in c:
            raise ValueError('p5-v1 currently requires the offline replay backend and replay_metadata')
        metadata = c['replay_metadata']
        if not isinstance(metadata, dict) or not all(metadata.get(k) for k in ('base_model', 'base_revision', 'quantization')):
            raise ValueError('replay_metadata requires base_model, base_revision and quantization')
        if metadata.get('base_revision_status', 'verified') not in ('verified', 'approximation'):
            raise ValueError('base_revision_status must be verified or approximation')
        if metadata['quantization'].get('load_in_4bit') is not True or metadata['quantization'].get('bnb_4bit_quant_type') != 'nf4':
            raise ValueError('replay requires the approved 4-bit NF4 base configuration')
        if not calibration_only and (metadata['quantization'].get('bnb_4bit_compute_dtype') not in ('float16', 'bfloat16', 'float32') or type(metadata['quantization'].get('bnb_4bit_use_double_quant')) is not bool):
            raise ValueError('replay_metadata must pin NF4 compute dtype and double-quant setting')
        if not all(re.fullmatch(r'[0-9a-f]{64}', metadata.get(k, '')) for k in ('tokenizer_sha256', 'chat_template_sha256')):
            raise ValueError('replay_metadata must pin tokenizer and chat-template SHA-256 digests')
        if c.get('legacy_manifest', False):
            if (metadata.get('model_dtype') != 'NOT RECORDED'
                    or metadata.get('device_map') != 'auto'
                    or metadata.get('gpu_devices_used') != 'NOT RECORDED'
                    or not re.fullmatch(r'[0-9a-f]{64}', metadata.get('legacy_runner_sha256', ''))):
                raise ValueError('legacy replay must mark unavailable runtime fields and pin the known runner SHA-256')
        elif metadata.get('model_dtype') != 'float16' or metadata.get('device_map') != {'': 0} or metadata.get('gpu_devices_used') != [0]:
            raise ValueError('p5-v1 requires float16 model dtype and a single-GPU device_map={"": 0}')
        expected = {'temperature': 0.0, 'seed': 42, 'num_predict': 2048, 'num_ctx': 8192}
        if c['generation_parameters'] != expected:
            raise ValueError(f'p5-v1 replay generation_parameters must be exactly {expected}')
        if len(c['models']) != 3 or sum(m['type'] == 'prompted' for m in c['models']) != 1 or sum(m['type'] == 'fine-tuned' for m in c['models']) != 2:
            raise ValueError('p5-v1 replay requires one prompted and two fine-tuned models')
        if any(m['type'] == 'fine-tuned' and not m.get('adapter_sha256') for m in c['models']):
            raise ValueError('each replayed fine-tuned model requires adapter_sha256')
    elif c['inference_backend'] != 'ollama':
        raise ValueError('offline replay currently requires p5-v1')
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
    return dict(tools=versions, models=[identity(c, m) for m in c['models']] if include_models and c.get('inference_backend', 'ollama') == 'ollama' else [])


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


def evaluate(c, model, case, directory, run_id, split, response_provider=None, format_mode='strict'):
    start = time.monotonic()
    folder = directory / case['id']
    folder.mkdir()
    record = dict(run_id=run_id, dataset_split=split, format_mode=format_mode, case_id=case['id'], vulnerability_class=case['class'], model_type=model['type'], model_tag=model['tag'], checkpoint_identity=model['checkpoint'], training_settings_provenance=model.get('training_settings_provenance', 'unspecified'), prompt_version=c['prompt_version'], temperature=c['generation_parameters']['temperature'], generation_parameters=c['generation_parameters'], timestamp=stamp(), raw_output_path=None, patch_path=None, raw_format_valid=None, valid_output=False, git_apply=False, functional_test_pass=None, attack_blocked=None, scanner_cleared=None, failure_reasons=[], execution_status='completed')
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
        prompt_provenance = None
        if c['prompt_version'] == 'p5-v1':
            prompt, prompt_provenance = build_case_prompts(case, original, baseline_scanner['findings'], spec['target'])
            prompt_bytes = json.dumps(prompt, sort_keys=True, ensure_ascii=False).encode('utf-8')
            record['prompt_sha256'] = hashlib.sha256(prompt_bytes).hexdigest()
            record['prompt_provenance'] = prompt_provenance
            (folder / 'prompt.json').write_text(json.dumps(prompt, ensure_ascii=False, indent=2))
        else:
            prompt = (ROOT / 'model-compare/prompts' / (c['prompt_version'] + '.txt')).read_text().format(filename=case['source'].name, vulnerability=case['class'], target=spec['target'], source=original)
            (folder / 'prompt.txt').write_text(prompt)
        try:
            if response_provider is not None:
                raw, provenance = response_provider(model, case, prompt)
                record['inference_provenance'] = provenance
            elif c['prompt_version'] == 'p5-v1':
                raise RuntimeError('p5-v1 responses must be supplied through offline replay')
            else:
                raw = generate(c, model, prompt)
        except (IdentityError, ReplayInputError):
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
        patch_input = raw
        if c['prompt_version'] == 'p5-v1':
            converted = function_response_to_diff(raw, original, case['source'].name, case['language'], spec['target'], format_mode=format_mode)
            record['raw_format_valid'] = converted['raw_format_valid']
            record['raw_format_failure_reasons'] = converted['failure_reasons']
            patch_input = converted['patch']
            if not converted['raw_format_valid']:
                record['failure_reasons'].extend(converted['failure_reasons'])
                record['execution_status'] = 'model_failure'
                return finalize(record)
        with tempfile.TemporaryDirectory(prefix='p6-patch-') as tmp:
            work = Path(tmp)
            validation = validate_patch(patch_input, original, case['source'].name, case['language'], spec['target'], work)
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
    c = read_config(args.config, calibration_only=args.action == 'calibrate-dev')
    if c['inference_backend'] == 'replay' and args.action == 'run':
        parser.error('use model-compare/replay.py for offline p5-v1 evaluation')
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
                if item['calibrated'] and c['prompt_version'] == 'p5-v1':
                    spec = json.loads(case['spec'].read_text())
                    prompt, provenance = build_case_prompts(case, case['source'].read_text(), item['scanner']['findings'], spec['target'])
                    prompt_path = directory / 'prompts' / (case['id'] + '.json')
                    prompt_path.parent.mkdir(parents=True, exist_ok=True)
                    prompt_bytes = json.dumps(prompt, sort_keys=True, ensure_ascii=False).encode('utf-8')
                    prompt_path.write_bytes(json.dumps(prompt, ensure_ascii=False, indent=2).encode('utf-8'))
                    item['prompt_sha256'] = hashlib.sha256(prompt_bytes).hexdigest()
                    item['prompt_provenance'] = provenance
                    item['prompt_artifact_path'] = str(prompt_path.relative_to(directory))
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
        metadata = preflight(c, include_models=c['inference_backend'] != 'replay')
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
