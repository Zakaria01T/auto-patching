def render_notification_html(value):
    from html import escape
    return "<div class=\"notification\">" + escape(value, quote=True) + "</div>"