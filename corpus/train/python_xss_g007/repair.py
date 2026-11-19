def error_message(detail):
    import html
    text = detail.strip()
    safe_text = html.escape(text, quote=True)
    box = "<div class='error'>{0}</div>".format(safe_text)
    return box
