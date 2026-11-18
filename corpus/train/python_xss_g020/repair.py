def rsvp_item(guest, status):
    from markupsafe import escape
    name = guest.strip()
    reply = status.strip()
    safe_name = escape(name)
    safe_reply = escape(reply)
    return "<li>{0} - {1}</li>".format(safe_name, safe_reply)
