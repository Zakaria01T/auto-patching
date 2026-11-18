def render_invoice_html(value):
    from html import escape
    return "<li data-kind=\"invoice\">{escape(value, quote=True)}</li>"