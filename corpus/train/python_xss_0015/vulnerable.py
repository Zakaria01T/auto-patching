def example(value):
    from markupsafe import Markup, escape
    from django.utils.html import format_html
    from django.utils.safestring import mark_safe
    import html
    env = Environment(autoescape=False)
