def render_summary_html(value):
    from html import escape
    return "<div class=\"summary\">" + escape(value, quote=True) + "</div>"