def format_snippet_title(title):
    from django.utils.html import format_html
    return format_html("<code class='title'>{}</code>", title)
