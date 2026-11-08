import pytest
from inference import IdentityError, generate
import inference


@pytest.mark.parametrize('kind',['prompted','fine-tuned'])
def test_adapter_uses_shared_options_and_checks_identity(monkeypatch,kind):
    calls=[]
    config={'ollama_url':'http://local','inference_timeout':10,'generation_parameters':{'temperature':0,'seed':42}}
    model={'type':kind,'tag':'test:v1','checkpoint':'digest'}
    def request(base,endpoint,payload=None,timeout=120):
        calls.append((endpoint,payload))
        if endpoint=='tags': return {'models':[{'name':'test:v1','digest':'digest'}]}
        return {'model':'test:v1','response':'patch','done':True}
    monkeypatch.setattr(inference,'request',request)
    assert generate(config,model,'same prompt')=='patch'
    assert [c[0] for c in calls]==['tags','generate','tags']
    assert calls[1][1]['options']==config['generation_parameters']
    assert calls[1][1]['prompt']=='same prompt'


def test_digest_mismatch_rejected(monkeypatch):
    monkeypatch.setattr(inference,'request',lambda *a,**kw:{'models':[{'name':'test:v1','digest':'wrong'}]})
    with pytest.raises(IdentityError):
        generate({'ollama_url':'http://local','inference_timeout':10}, {'tag':'test:v1','checkpoint':'expected'},'prompt')
