def download_video():
    import subprocess
    from flask import request
    url = request.form["url"]
    output = request.form.get("output", "%(title)s.%(ext)s")
    subprocess.run(["youtube-dl", "-o", output, "--", url], check=True)
