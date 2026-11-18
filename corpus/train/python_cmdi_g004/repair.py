def video_thumbnail():
    import subprocess
    from flask import request
    video = request.form["video"]
    subprocess.run(["ffmpeg", "-y", "-i", video, "-ss", "00:00:01", "-vframes", "1", "/tmp/thumb.jpg"], check=True)
    return "/tmp/thumb.jpg"
