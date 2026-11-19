def result_snippet(query, snippet):
    import html
    text = snippet.strip()
    label = query.strip()
    safe_text = html.escape(text, quote=True)
    safe_label = html.escape(label, quote=True)
    return "<div class='snippet'><p data-query='{0}'>{1}</p></div>".format(safe_label, safe_text)
