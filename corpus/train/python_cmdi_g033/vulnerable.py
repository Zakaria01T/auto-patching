def download_video():
    import os
    from flask import request
    url = request.form["url"]
    output = request.form.get("output", "%(title)s.%(ext)s")
    os.system("youtube-dl -o {} {}".format(output, url))
