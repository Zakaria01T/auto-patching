import difflib
import json
from pathlib import Path
import sys

import pytest

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
from evaluation import CLASSES, METRICS, aggregate, finalize, load_cases, validate_patch
import run

ORIGINAL = 'def repair(x):\n    return x\n'
CHANGED = 'def repair(x):\n    return x + 1\n'


def patch(old=ORIGINAL, new=CHANGED):
    return ''.join(difflib.unified_diff(old.splitlines(True), new.splitlines(True), fromfile='a/source.py', tofile='b/source.py'))


@pytest.mark.parametrize('raw,reason', [('', 'empty_output'), (ORIGINAL,'no_change'), ('broken', 'malformed_patch'), (patch('def repair(x):\n    return x + 5\n'), 'git_apply_failed')])
def test_invalid(tmp_path, raw, reason):
    result = validate_patch(raw, ORIGINAL, 'source.py', 'python', 'repair', tmp_path)
    assert not result['valid_output'] and reason in result['failure_reasons']


def test_changed_accepted(tmp_path):
    result = validate_patch('```diff\n' + patch() + '```', ORIGINAL, 'source.py', 'python', 'repair', tmp_path)
    assert result['valid_output'] and result['git_apply']


def test_unrelated_only(tmp_path):
    result = validate_patch(patch(new='import os\n' + ORIGINAL), ORIGINAL, 'source.py', 'python', 'repair', tmp_path)
    assert result['failure_reasons'] == ['wrong_target']


def test_comment_only(tmp_path):
    result = validate_patch(patch(new=ORIGINAL + '# comment\n'), ORIGINAL, 'source.py', 'python', 'repair', tmp_path)
    assert not result['valid_output']


def record(cls='xss', **kw):
    return finalize(dict(dataset_split='dev', model_type='prompted', model_tag='test:1', vulnerability_class=cls, execution_status='completed', failure_reasons=[], **dict({k:True for k in METRICS[:4]}, **kw)))


@pytest.mark.parametrize('metric', ['valid_output','functional_test_pass','attack_blocked'])
def test_fix_requires_all(metric):
    assert not record(**{metric:False})['fix_success']


def test_scanner_independent():
    r = record(scanner_cleared=False)
    assert r['fix_success']
    rows = aggregate([r])
    overall = rows[-1]
    assert overall['scanner_cleared_percent'] == 0
    assert overall['fix_success_percent'] == 100


def test_weighted_counts_and_skips():
    rows = aggregate([record('xss'),record('xss',attack_blocked=False),record('sql_injection',functional_test_pass=None)])
    overall = rows[-1]
    assert overall['total'] == 3
    assert overall['fix_success_numerator'] == 1
    assert overall['fix_success_percent'] == pytest.approx(100/3)
    assert overall['functional_test_pass_skipped'] == 1
    assert next(r for r in rows if r['vulnerability_class']=='xss')['fix_success_percent'] == 50


def test_infrastructure_suppresses_scores():
    r = record()
    r.update(execution_status='infrastructure_error', failure_reasons=['infrastructure_error'])
    assert aggregate([r])[-1]['fix_success_percent'] is None
    assert not aggregate([r])[-1]['publishable']


def test_no_mixed_datasets():
    r = record(); r['dataset_split'] = 'benchmark'
    with pytest.raises(ValueError): aggregate([record(),r])
    with pytest.raises(ValueError): load_cases('benchmark')
    with pytest.raises(ValueError): load_cases('other')


def test_dev_cases():
    cases = load_cases('dev')
    assert len(cases) == 32
    assert {c['class'] for c in cases} == set(CLASSES)
    for c in cases:
        assert json.loads(c['spec'].read_text())['test_sha256'] == run.digest(c['test'])


@pytest.mark.parametrize('kind', ['prompted','fine-tuned'])
def test_both_models_share_pipeline(monkeypatch, tmp_path, kind):
    case = load_cases('dev')[0]
    # Fail calibration deterministically; both types take the exact same checks.
    calls = []
    def check(config, folder, mode):
        calls.append(mode)
        return {'passed': True} if mode != 'scanner' else {'findings':[]}
    monkeypatch.setattr(run, 'check', check)
    config = {'prompt_version':'v1','generation_parameters':{'temperature':0}}
    r = run.evaluate(config, {'type':kind,'tag':'test','checkpoint':'digest'}, case, tmp_path, 'id', 'dev')
    assert calls == ['functional','attack','scanner']
    assert r['execution_status'] == 'infrastructure_error'
    assert r['failure_reasons'] == ['infrastructure_error']
    assert r['duration_seconds'] >= 0


def test_container_restrictions():
    argv = run.docker_base({'memory':'1g','cpus':1,'pids_limit':64})
    assert '--network=none' in argv and '--read-only' in argv
    assert '--cap-drop=ALL' in argv
    assert not any(':/repo:ro' in item for item in argv)


def test_final_requires_freeze_and_authorization(monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['run.py','run','--dataset','benchmark'])
    with pytest.raises(SystemExit) as exc: run.main()
    assert exc.value.code == 2


@pytest.mark.parametrize('kind', ['prompted','fine-tuned'])
def test_successful_shared_pipeline_scanner_persists(monkeypatch, tmp_path, kind):
    case = next(c for c in load_cases('dev') if c['id'] == 'xss_01')
    seen = []
    finding = {'cwe':case['cwe'],'rule_id':'original-rule'}
    def check(config, folder, mode):
        seen.append(mode)
        if mode == 'scanner': return {'findings':[finding]}
        if len(seen) == 2: return {'passed':False, 'reason':'attack_not_blocked'}
        return {'passed':True}
    original = case['source'].read_text()
    changed = original.replace(' + name + ', ' + str(name) + ')
    raw = ''.join(difflib.unified_diff(original.splitlines(True),changed.splitlines(True),fromfile='a/source.py',tofile='b/source.py'))
    monkeypatch.setattr(run, 'check', check)
    monkeypatch.setattr(run, 'generate', lambda *args:raw)
    r = run.evaluate({'prompt_version':'v1','generation_parameters':{'temperature':0}}, {'type':kind,'tag':'test','checkpoint':'digest'}, case, tmp_path, 'id', 'dev')
    assert seen == ['functional','attack','scanner'] * 2
    assert r['fix_success'] and not r['scanner_cleared']
    assert r['failure_reasons'] == ['scanner_finding_persisted']
    assert r['execution_status'] == 'completed'
    assert (tmp_path / case['id'] / 'raw.txt').read_text() == raw


def test_c_target_ignores_comments_and_braces_in_literals():
    from evaluation import target_body
    original = 'void copy_name(char *x) { puts("}"); }'
    assert target_body(original,'c','copy_name') == target_body('// copy_name(x) { fake; }\n' + original,'c','copy_name')


def test_report_outputs(tmp_path):
    from evaluation import reports
    reports([record(scanner_cleared=False)], tmp_path)
    assert (tmp_path/'summary.csv').read_text().startswith('model,')
    assert '# DEV' in (tmp_path/'report.md').read_text()
    assert len((tmp_path/'records.jsonl').read_text().splitlines()) == 1


def test_identity_drift_is_infrastructure(monkeypatch, tmp_path):
    from inference import IdentityError
    case = load_cases('dev')[0]
    def check(c,folder,mode):
        return {'findings':[{'cwe':case['cwe'],'rule_id':'r'}]} if mode=='scanner' else {'passed':mode=='functional'}
    def generate(*args): raise IdentityError('drift')
    monkeypatch.setattr(run,'check',check)
    monkeypatch.setattr(run,'generate',generate)
    r = run.evaluate({'prompt_version':'v1','generation_parameters':{'temperature':0}}, {'type':'prompted','tag':'test','checkpoint':'digest'},case,tmp_path,'id','dev')
    assert r['execution_status']=='infrastructure_error'


def test_dataset_symlink_rejected(monkeypatch, tmp_path):
    import evaluation
    (tmp_path/'corpus').mkdir()
    (tmp_path/'benchmark').mkdir()
    (tmp_path/'corpus/dev').symlink_to(tmp_path/'benchmark',target_is_directory=True)
    monkeypatch.setattr(evaluation,'ROOT',tmp_path)
    with pytest.raises(ValueError,match='symlink'): evaluation.load_cases('dev')


def test_benchmark_missing_case_metadata_rejected(monkeypatch,tmp_path):
    import evaluation
    (tmp_path/'benchmark/missing').mkdir(parents=True)
    monkeypatch.setattr(evaluation,'ROOT',tmp_path)
    with pytest.raises(ValueError,match='metadata'): evaluation.load_cases('benchmark',True)


def test_empty_benchmark_rejected_after_authorization(monkeypatch,tmp_path):
    import evaluation
    (tmp_path/'benchmark').mkdir()
    monkeypatch.setattr(evaluation,'ROOT',tmp_path)
    with pytest.raises(ValueError,match='empty'): evaluation.load_cases('benchmark',True)


def test_writable_tmpfs_and_unprivileged_ping():
    argv=run.docker_base({'memory':'1g','cpus':1,'pids_limit':64})
    assert '--tmpfs=/work:rw,exec,nosuid,size=64m,mode=1777' in argv
    assert '--sysctl=net.ipv4.ping_group_range=0 2147483647' in argv


def test_infrastructure_preflight_records_all_assigned_cases(monkeypatch,tmp_path):
    config=json.loads((BASE/'config.example.json').read_text())
    config['image']='sha256:'+'a'*64
    path=tmp_path/'config.json'; path.write_text(json.dumps(config))
    output=tmp_path/'results'
    monkeypatch.setattr(sys,'argv',['run.py','run','--config',str(path),'--output-dir',str(output)])
    def fail(*args): raise RuntimeError('missing runtime')
    monkeypatch.setattr(run,'preflight',fail)
    with pytest.raises(SystemExit) as exc: run.main()
    assert exc.value.code==2
    directory=next((output/'dev').iterdir())
    records=[json.loads(line) for line in (directory/'records.jsonl').read_text().splitlines()]
    assert len(records)==64
    assert all(r['execution_status']=='infrastructure_error' for r in records)
    summary=json.loads((directory/'summary.json').read_text())
    assert all(r['fix_success_percent'] is None for r in summary)
    assert all(r['total']==32 for r in summary if r['vulnerability_class']=='OVERALL')


def test_config_and_freeze_drift_rejected(monkeypatch,tmp_path):
    config=json.loads((BASE/'config.example.json').read_text())
    config['image']='sha256:'+'b'*64
    path=tmp_path/'config.json';path.write_text(json.dumps(config))
    frozen=tmp_path/'freeze.json';frozen.write_text(json.dumps({'config':config,'code_hashes':{}}))
    monkeypatch.setattr(sys,'argv',['run.py','run','--config',str(path),'--frozen',str(frozen)])
    with pytest.raises(ValueError,match='frozen'): run.main()
