def example(value):
    from markupsafe import Markup, escape
    from django.utils.html import format_html
    import html
    import bleach
    env = Environment(autoescape=select_autoescape(["html", "htm", "xml"]))
