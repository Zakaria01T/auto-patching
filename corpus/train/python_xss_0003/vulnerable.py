def render_account_html(value):
    from django.utils.safestring import mark_safe
    return mark_safe("<span>account: " + value + "</span>")