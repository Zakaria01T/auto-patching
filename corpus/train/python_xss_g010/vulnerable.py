def job_link():
    url = request.args.get("url", "")
    url = url.strip()
    return f"<div class='job'><a href='{url}'>View job</a></div>"
