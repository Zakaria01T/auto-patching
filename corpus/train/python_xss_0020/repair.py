def render_event_html(value):
    from html import escape
    return "<div class=\"event\">" + escape(value, quote=True) + "</div>"