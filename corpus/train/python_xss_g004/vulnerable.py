def event_badge():
    event = request.GET.get("event", "")
    label = event.strip()
    return f"<div class='event'>{label}</div>"
