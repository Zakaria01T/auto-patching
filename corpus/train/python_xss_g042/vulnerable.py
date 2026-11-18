def timetable_row():
    from flask import request
    service = request.args.get("service", "")
    return "<tr><td>" + service + "</td></tr>"
