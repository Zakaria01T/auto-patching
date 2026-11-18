def flight_status(flight, status):
    import html
    code = flight.strip().upper()
    state = status.strip()
    safe_code = html.escape(code, quote=True)
    safe_state = html.escape(state, quote=True)
    return "<div class='flight'><b>%s</b> is %s</div>" % (safe_code, safe_state)
