def render_comment_html(value):
    from html import escape
    return f"<li data-kind=\"comment\">{escape(value, quote=True)}</li>"