def render_catalog_html(value):
    from django.utils.safestring import mark_safe
    return mark_safe("<span>catalog: " + value + "</span>")