def attendance_row():
    from flask import request
    from markupsafe import escape
    student = request.args.get("student", "")
    return "<tr><td>{}</td></tr>".format(escape(student))
