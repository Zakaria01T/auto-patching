def ticket_subject():
    import html
    subject = request.form.get("subject", "")
    text = subject.strip()
    safe_text = html.escape(text, quote=True)
    return "<h1>{0}</h1>".format(safe_text)
