def book_entry(title, author):
    import html
    name = title.strip()
    writer = author.strip()
    safe_name = html.escape(name, quote=True)
    safe_writer = html.escape(writer, quote=True)
    return "<li><b>{0}</b> by {1}</li>".format(safe_name, safe_writer)
