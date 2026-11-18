def fetch_remote_text(url: str) -> str:
    from urllib.parse import urlparse
    from urllib.request import urlopen
    if urlparse(url).scheme not in ("http", "https"):
        raise ValueError("Invalid URL scheme")
    with urlopen(url, timeout=10) as resp:
        return resp.read().decode("utf-8", errors="replace")