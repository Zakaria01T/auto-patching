def render_notice(message: str):
    from django.utils.html import format_html
    return format_html(f"<div class='notice'>{message}</div>")