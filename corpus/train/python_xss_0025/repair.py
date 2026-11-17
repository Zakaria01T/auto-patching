def render_catalog_html(value):
    from django.utils.html import format_html
    return format_html("<span>catalog: {}</span>", value)