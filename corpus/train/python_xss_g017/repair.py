def headline(title):
    import html
    slug = title.strip()
    safe_slug = html.escape(slug, quote=True)
    markup = "<h2 class='headline'>{0}</h2>".format(safe_slug)
    return markup
