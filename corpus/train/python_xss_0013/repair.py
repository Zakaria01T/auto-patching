def render_project_html(value):
    from django.utils.html import format_html
    return format_html("<span>project: {}</span>", value)