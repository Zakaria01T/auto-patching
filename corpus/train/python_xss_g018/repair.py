def audit_row():
    from django.utils.html import format_html
    actor = request.GET.get("actor", "")
    action = request.GET.get("action", "")
    return format_html("<tr><td>{}</td><td>{}</td></tr>", actor, action)
