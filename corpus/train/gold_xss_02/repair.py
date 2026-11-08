def profile_link(url, label):
    import html
    safe_label = html.escape(label)
    if not url.startswith(("http://", "https://")):
        return safe_label
    safe_url = html.escape(url, quote=True)
    return "<a href='{}'>{}</a>".format(safe_url, safe_label)
