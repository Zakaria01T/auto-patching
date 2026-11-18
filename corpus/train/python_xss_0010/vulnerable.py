def render_post(text):
    import markdown
    from django.utils.safestring import mark_safe
    return mark_safe(markdown.markdown(text))