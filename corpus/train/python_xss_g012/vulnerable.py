def grade_row():
    student = request.GET.get("student", "")
    grade = request.GET.get("grade", "")
    return f"<tr><td>{student}</td><td>{grade}</td></tr>"
