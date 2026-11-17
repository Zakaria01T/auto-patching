def render_status_html(value):
    from django.utils.safestring import mark_safe
    return mark_safe("<span>status: " + value + "</span>")