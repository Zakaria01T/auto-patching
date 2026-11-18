def download(url):
    import urllib.request
    from urllib.parse import urlparse
    if urlparse(url).scheme not in ("http", "https"):
        raise ValueError("unsupported URL scheme")
    urllib.request.urlretrieve(url, "page.html")