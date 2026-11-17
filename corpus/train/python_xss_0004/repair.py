def render_profile_html(value):
    from html import escape
    return "<div class=\"profile\">" + escape(value, quote=True) + "</div>"