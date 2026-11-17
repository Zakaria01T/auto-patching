def render_report_html(value):
    from django.utils.safestring import mark_safe
    return mark_safe("<span>report: " + value + "</span>")