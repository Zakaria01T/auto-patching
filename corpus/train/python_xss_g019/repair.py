def wiki_title():
    import html
    title = request.args.get("title", "")
    text = title.strip()
    safe_text = html.escape(text, quote=True)
    markup = "<h1 class='wiki'>{0}</h1>".format(safe_text)
    return markup
