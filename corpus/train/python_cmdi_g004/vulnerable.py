def video_thumbnail():
    import os
    from flask import request
    video = request.form["video"]
    cmd = f"ffmpeg -y -i {video} -ss 00:00:01 -vframes 1 /tmp/thumb.jpg"
    os.system(cmd)
    return "/tmp/thumb.jpg"
