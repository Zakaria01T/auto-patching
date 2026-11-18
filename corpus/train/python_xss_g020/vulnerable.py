def rsvp_item(guest, status):
    name = guest.strip()
    reply = status.strip()
    return f"<li>{name} - {reply}</li>"
