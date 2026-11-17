def render_blog_html(value):
    from html import escape
    return f"<li data-kind=\"blog\">{escape(value, quote=True)}</li>"