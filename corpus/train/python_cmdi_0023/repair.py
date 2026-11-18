def grab(link):
    import requests
    resp = requests.get(link, timeout=10)
    resp.raise_for_status()
    return resp.content