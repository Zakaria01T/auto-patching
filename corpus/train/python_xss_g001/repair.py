def render_forum_post(title):
    import html
    heading = "<article><h2>{0}</h2><p>Join the discussion.</p>".format(html.escape(title, quote=True))
    body = heading.strip()
    return body
