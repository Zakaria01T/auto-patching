def link_html(link, title):
    from django.utils.safestring import mark_safe
    return mark_safe(f"<a href='{link}'>{title}</a>")