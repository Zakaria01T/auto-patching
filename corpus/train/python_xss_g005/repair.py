def profile_badge(username):
    from markupsafe import escape
    name = username.strip()
    display = name
    safe_display = escape(display)
    return "<span class='badge'>{0}</span>".format(safe_display)
