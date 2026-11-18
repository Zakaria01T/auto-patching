def format_snippet_title(title):
    from django.template import Context
    ctx = Context({'title': title})
    return f"<code class='title'>{title}</code>"
