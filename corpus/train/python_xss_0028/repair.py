def render_billing_html(value):
    from html import escape
    return "<div class=\"billing\">" + escape(value, quote=True) + "</div>"