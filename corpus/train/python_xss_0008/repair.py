def render_ticket_html(value):
    from html import escape
    return "<div class=\"ticket\">" + escape(value, quote=True) + "</div>"