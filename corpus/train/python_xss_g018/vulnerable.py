def audit_row():
    actor = request.GET.get("actor", "")
    action = request.GET.get("action", "")
    return f"<tr><td>{actor}</td><td>{action}</td></tr>"
