def grade_row():
    from django.utils.html import format_html
    student = request.GET.get("student", "")
    grade = request.GET.get("grade", "")
    return format_html("<tr><td>{}</td><td>{}</td></tr>", student, grade)
