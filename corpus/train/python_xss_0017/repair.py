def render_review_html(value):
    from django.utils.html import format_html
    return format_html("<span>review: {}</span>", value)