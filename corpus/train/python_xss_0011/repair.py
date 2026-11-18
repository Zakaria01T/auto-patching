def link_html(link, title):
    from django.utils.html import format_html
    return format_html("<a href='{}'>{}</a>", link, title)