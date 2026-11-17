def render_project_html(value):
    from django.utils.safestring import mark_safe
    return mark_safe("<span>project: " + value + "</span>")