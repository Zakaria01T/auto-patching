def render_report_html(value):
    from django.utils.html import format_html
    return format_html("<span>report: {}</span>", value)