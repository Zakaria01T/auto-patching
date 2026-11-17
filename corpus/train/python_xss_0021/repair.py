def render_member_html(value):
    from django.utils.html import format_html
    return format_html("<span>member: {}</span>", value)