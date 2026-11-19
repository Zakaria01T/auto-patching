def ticket_subject():
    subject = request.form.get("subject", "")
    text = subject.strip()
    return "<h1>" + text + "</h1>"
