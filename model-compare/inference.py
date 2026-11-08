"""Model-specific transport; both model types use this same Ollama adapter."""
import json
import urllib.request


class IdentityError(RuntimeError):
    pass


def request(base, endpoint, payload=None, timeout=120):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(base.rstrip('/') + '/api/' + endpoint, data=data, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.load(response)


def identity(config, model):
    tags = request(config['ollama_url'], 'tags', timeout=config['inference_timeout'])['models']
    matches = [x for x in tags if x['name'] == model['tag'] and x['digest'] == model['checkpoint']]
    if len(matches) != 1:
        raise IdentityError('model tag/checkpoint mismatch or model not installed: ' + model['tag'])
    return matches[0]


def generate(config, model, prompt):
    identity(config, model)
    result = request(config['ollama_url'], 'generate', {
        'model': model['tag'], 'prompt': prompt, 'stream': False,
        'options': config['generation_parameters'],
    }, config['inference_timeout'])
    identity(config, model)
    if result.get('model') != model['tag'] or result.get('done') is not True or not isinstance(result.get('response'), str):
        raise RuntimeError('incomplete generation or unexpected model identity')
    return result['response']
