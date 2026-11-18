def result_snippet(query, snippet):
    text = snippet.strip()
    label = query.strip()
    return f"<div class='snippet'><p data-query='{label}'>{text}</p></div>"
