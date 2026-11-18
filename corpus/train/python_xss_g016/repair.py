def weather_widget():
    import html
    from urllib.parse import urlparse
    icon = request.args.get("icon", "")
    icon = icon.strip()
    parsed = urlparse(icon)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return ""
    safe_icon = html.escape(icon, quote=True)
    return "<div class='weather'><img src='{0}' alt='weather'></div>".format(safe_icon)
