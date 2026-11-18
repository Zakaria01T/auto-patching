def event_badge():
    from django.utils.html import format_html
    event = request.GET.get("event", "")
    label = event.strip()
    return format_html("<div class='event'>{}</div>", label)
