def render_status_html(value):
    from django.utils.html import format_html
    return format_html("<span>status: {}</span>", value)