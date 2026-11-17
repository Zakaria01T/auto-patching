def render_product_html(value):
    from html import escape
    return "<div class=\"product\">" + escape(value, quote=True) + "</div>"