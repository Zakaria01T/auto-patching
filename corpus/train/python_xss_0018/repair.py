def render_support_html(value):
    from html import escape
    return f"<li data-kind=\"support\">{escape(value, quote=True)}</li>"