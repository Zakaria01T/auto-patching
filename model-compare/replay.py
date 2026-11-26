#!/usr/bin/env python3
"""Replay saved HF/PEFT generations through the DEV Docker checks and P1 metrics."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import uuid

from evaluation import ROOT, digest, finalize, load_cases, reports
import run as harness
from p5_eval import ReplayInputError


def _prompt_hash(prompt):
    return hashlib.sha256(json.dumps(prompt, sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest()


def load_replay_outputs(path, config, cases):
    """Validate a complete, three-model, 32-case Kaggle output JSONL before replay."""
    models = {m['tag']: m for m in config['models']}
    case_ids = {c['id'] for c in cases}
    metadata = config['replay_metadata']
    expected_generation = config['generation_parameters']
    required = {
        'case_id', 'model_type', 'model_tag', 'checkpoint_identity', 'base_model',
        'base_revision', 'base_revision_status', 'quantization', 'adapter_sha256', 'tokenizer_sha256',
        'model_dtype', 'device_map', 'gpu_devices_used', 'training_settings_provenance',
        'chat_template_sha256', 'prompt_version', 'generation_parameters',
        'decoding', 'seed_applied', 'input_tokens', 'model_input_sha256', 'prompt', 'prompt_sha256', 'raw_output', 'library_versions',
    }
    rows = {}
    versions = None
    for line_number, line in enumerate(Path(path).read_text(encoding='utf-8').splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ReplayInputError(f'line {line_number}: invalid JSON: {exc}') from exc
        missing = required - set(row)
        if missing:
            raise ReplayInputError(f'line {line_number}: missing fields {sorted(missing)}')
        tag = row['model_tag']
        if tag not in models:
            raise ReplayInputError(f'line {line_number}: unknown model tag {tag!r}')
        model = models[tag]
        case_id = row['case_id']
        if case_id not in case_ids:
            raise ReplayInputError(f'line {line_number}: case is not in DEV: {case_id!r}')
        key = (tag, case_id)
        if key in rows:
            raise ReplayInputError(f'line {line_number}: duplicate model/case record {key}')
        if row['model_type'] != model['type'] or row['checkpoint_identity'] != model['checkpoint']:
            raise ReplayInputError(f'line {line_number}: model identity differs from config')
        if row['base_model'] != metadata['base_model'] or row['base_revision'] != metadata['base_revision']:
            raise ReplayInputError(f'line {line_number}: base model identity differs from config')
        if row['base_revision_status'] != metadata.get('base_revision_status', 'verified'):
            raise ReplayInputError(f'line {line_number}: base revision provenance status differs from config')
        if row['quantization'] != metadata['quantization']:
            raise ReplayInputError(f'line {line_number}: quantization differs from config')
        if row['model_dtype'] != metadata['model_dtype'] or row['device_map'] != metadata['device_map'] or row['gpu_devices_used'] != metadata['gpu_devices_used']:
            raise ReplayInputError(f'line {line_number}: model dtype or device map differs from config')
        if row['training_settings_provenance'] != model.get('training_settings_provenance', 'unspecified'):
            raise ReplayInputError(f'line {line_number}: training settings provenance differs from config')
        if row['adapter_sha256'] != model.get('adapter_sha256'):
            raise ReplayInputError(f'line {line_number}: adapter SHA-256 differs from config')
        if row['tokenizer_sha256'] != metadata['tokenizer_sha256'] or row['chat_template_sha256'] != metadata['chat_template_sha256']:
            raise ReplayInputError(f'line {line_number}: tokenizer or chat-template digest differs from config')
        if row['prompt_version'] != 'p5-v1' or row['generation_parameters'] != expected_generation:
            raise ReplayInputError(f'line {line_number}: prompt version or generation parameters differ from config')
        expected_decoding = {'do_sample': False, 'max_new_tokens': expected_generation['num_predict'], 'context_limit': expected_generation['num_ctx']}
        if row['decoding'] != expected_decoding:
            raise ReplayInputError(f'line {line_number}: HF decoding settings differ from config')
        if row['seed_applied'] != expected_generation['seed']:
            raise ReplayInputError(f'line {line_number}: applied seed differs from config')
        if type(row['input_tokens']) is not int or row['input_tokens'] < 0 or row['input_tokens'] + expected_generation['num_predict'] > expected_generation['num_ctx']:
            raise ReplayInputError(f'line {line_number}: prompt plus max_new_tokens exceeds the frozen context limit')
        if not isinstance(row['model_input_sha256'], str) or not re.fullmatch(r'[0-9a-f]{64}', row['model_input_sha256']):
            raise ReplayInputError(f'line {line_number}: model_input_sha256 must be a lowercase SHA-256 digest')
        prompt = row['prompt']
        if not isinstance(prompt, dict) or set(prompt) != {'system', 'user'} or not all(isinstance(prompt[k], str) for k in prompt):
            raise ReplayInputError(f'line {line_number}: prompt must contain system and user strings')
        if row['prompt_sha256'] != _prompt_hash(prompt):
            raise ReplayInputError(f'line {line_number}: prompt SHA-256 mismatch')
        if not isinstance(row['raw_output'], str) or not isinstance(row['library_versions'], dict) or not row['library_versions']:
            raise ReplayInputError(f'line {line_number}: raw_output or library_versions is invalid')
        if versions is None:
            versions = row['library_versions']
        elif versions != row['library_versions']:
            raise ReplayInputError('inference library versions differ across saved generations')
        rows[key] = row
    expected = {(tag, case_id) for tag in models for case_id in case_ids}
    missing = expected - set(rows)
    extra = set(rows) - expected
    if missing or extra:
        raise ReplayInputError(f'incomplete replay matrix: missing={sorted(missing)} extra={sorted(extra)}')
    for case_id in case_ids:
        prompts = {json.dumps(rows[(tag, case_id)]['prompt'], sort_keys=True, ensure_ascii=False) for tag in models}
        if len(prompts) != 1:
            raise ReplayInputError(f'prompts differ across models for case {case_id}')
        input_hashes = {rows[(tag, case_id)]['model_input_sha256'] for tag in models}
        if len(input_hashes) != 1:
            raise ReplayInputError(f'tokenized model inputs differ across models for case {case_id}')
    return rows, versions


def _infra_record(config, model, case, run_id, error):
    return finalize(dict(
        run_id=run_id, dataset_split='dev', case_id=case['id'],
        vulnerability_class=case['class'], model_type=model['type'],
        model_tag=model['tag'], checkpoint_identity=model['checkpoint'],
        training_settings_provenance=model.get('training_settings_provenance', 'unspecified'),
        prompt_version=config['prompt_version'],
        temperature=config['generation_parameters']['temperature'],
        generation_parameters=config['generation_parameters'],
        timestamp=datetime.now(timezone.utc).isoformat(), raw_output_path=None,
        patch_path=None, raw_format_valid=None, valid_output=False,
        git_apply=False, functional_test_pass=None, attack_blocked=None,
        scanner_cleared=None, failure_reasons=['infrastructure_error'],
        execution_status='infrastructure_error', error=error, duration_seconds=0,
    ))


def run_replay(config_path, input_path, output_dir, frozen_path):
    config = harness.read_config(config_path)
    if config['inference_backend'] != 'replay' or config['prompt_version'] != 'p5-v1':
        raise ValueError('replay requires a p5-v1 config with inference_backend=replay')
    frozen = json.loads(Path(frozen_path).read_text(encoding='utf-8'))
    code_hashes = harness.code_hashes()
    if frozen.get('config') != config or frozen.get('code_hashes') != code_hashes:
        raise ValueError('frozen configuration or evaluator changed; freeze again before replay')
    cases = load_cases('dev')
    outputs, library_versions = load_replay_outputs(input_path, config, cases)
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S') + '-' + uuid.uuid4().hex[:12]
    directory = Path(output_dir).resolve() / 'dev' / run_id
    directory.mkdir(parents=True, exist_ok=False)
    manifest = dict(
        run_id=run_id, dataset_split='dev', config=config,
        code_hashes=code_hashes, timestamp=datetime.now(timezone.utc).isoformat(),
        repository_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        repository_dirty=bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True)),
        frozen_sha256=digest(frozen_path), replay_input_sha256=digest(input_path), replay_library_versions=library_versions,
        cases={case['id']:{p.name:digest(p) for p in (case['source'], case['test'], case['spec'], case['source'].parent/'meta.json')} for case in cases},
    )
    infrastructure_error = None
    try:
        manifest['environment'] = harness.preflight(config, include_models=False)
        if manifest['environment'] != frozen.get('environment'):
            raise RuntimeError('frozen Docker tool environment changed')
    except Exception as exc:
        infrastructure_error = str(exc)
        manifest['infrastructure_error'] = infrastructure_error
    (directory / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    records = []
    for model in config['models']:
        model_dir = directory / (model['type'] + '-' + model['tag'])
        model_dir.mkdir(parents=True)
        for case in cases:
            if infrastructure_error:
                record = _infra_record(config, model, case, run_id, infrastructure_error)
            else:
                def response_provider(selected_model, selected_case, prompt):
                    row = outputs[(selected_model['tag'], selected_case['id'])]
                    if prompt != row['prompt']:
                        raise ReplayInputError('saved prompt differs from locally rebuilt p5-v1 prompt')
                    provenance = {k: row[k] for k in (
                        'base_model', 'base_revision', 'base_revision_status', 'quantization', 'model_dtype',
                        'device_map', 'gpu_devices_used', 'training_settings_provenance', 'adapter_sha256',
                        'tokenizer_sha256', 'chat_template_sha256', 'generation_parameters',
                        'decoding', 'seed_applied', 'input_tokens', 'model_input_sha256',
                        'library_versions', 'prompt_sha256',
                    )}
                    return row['raw_output'], provenance
                record = harness.evaluate(config, model, case, model_dir, run_id, 'dev', response_provider=response_provider)
            records.append(record)
            with (directory / 'journal.jsonl').open('a', encoding='utf-8') as stream:
                stream.write(json.dumps(record, sort_keys=True) + '\n')
    reports(records, directory)
    print(directory)
    if any(record['execution_status'] == 'infrastructure_error' for record in records):
        raise SystemExit(2)
    return directory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--input-jsonl', type=Path, required=True)
    parser.add_argument('--frozen', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'model-compare/results')
    args = parser.parse_args()
    run_replay(args.config, args.input_jsonl, args.output_dir, args.frozen)


if __name__ == '__main__':
    main()
