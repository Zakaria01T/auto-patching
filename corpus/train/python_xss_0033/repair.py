def render_notice(message: str):
    from django.utils.html import format_html
    return format_html("<div class='notice'>{}</div>", message)