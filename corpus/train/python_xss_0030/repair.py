def render_settings_html(value):
    from html import escape
    return f"<li data-kind=\"settings\">{escape(value, quote=True)}</li>"