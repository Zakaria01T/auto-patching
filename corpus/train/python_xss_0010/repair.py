def render_invoice_html(value):
    from html import escape
    return f"<li data-kind=\"invoice\">{escape(value, quote=True)}</li>"