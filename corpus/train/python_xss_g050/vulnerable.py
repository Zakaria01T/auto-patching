def attendance_row():
    from flask import request
    student = request.args.get("student", "")
    return "<tr><td>" + student + "</td></tr>"
