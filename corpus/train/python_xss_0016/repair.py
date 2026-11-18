def example(value):
    from markupsafe import Markup, escape
    from django.utils.html import format_html
    import html
    import bleach
    return format_html("<aside>{}</aside>", notice_text)
