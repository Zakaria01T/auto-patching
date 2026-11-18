def job_link():
    import html
    from urllib.parse import urlparse
    url = request.args.get("url", "")
    url = url.strip()
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return ""
    safe_url = html.escape(url, quote=True)
    return "<div class='job'><a href='{0}'>View job</a></div>".format(safe_url)
