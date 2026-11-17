def render_member_html(value):
    from django.utils.safestring import mark_safe
    return mark_safe("<span>member: " + value + "</span>")