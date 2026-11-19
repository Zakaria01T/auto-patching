def build_author_badge(username: str, role: str):
    from django.utils.safestring import mark_safe
    return mark_safe(f"<span class='badge'>{username} ({role})</span>")