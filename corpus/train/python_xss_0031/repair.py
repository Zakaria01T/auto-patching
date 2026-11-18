def build_author_badge(username: str, role: str):
    from django.utils.html import format_html
    return format_html("<span class='badge'>{} ({})</span>", username, role)