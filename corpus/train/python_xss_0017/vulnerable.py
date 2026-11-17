def render_review_html(value):
    from django.utils.safestring import mark_safe
    return mark_safe("<span>review: " + value + "</span>")