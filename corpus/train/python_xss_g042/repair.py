def timetable_row():
    import html
    from flask import request
    service = request.args.get("service", "")
    return "<tr><td>{}</td></tr>".format(html.escape(service, quote=True))
