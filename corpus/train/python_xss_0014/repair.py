def render_team_html(value):
    from html import escape
    return f"<li data-kind=\"team\">{escape(value, quote=True)}</li>"