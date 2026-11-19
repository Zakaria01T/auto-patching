def chat_line(sender, text):
    import html
    name = sender.strip()
    body = text.strip()
    safe_name = html.escape(name, quote=True)
    safe_body = html.escape(body, quote=True)
    return "<p><strong>{0}</strong>: {1}</p>".format(safe_name, safe_body)
