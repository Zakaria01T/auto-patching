def archive_folder():
    import os
    from flask import request
    folder = request.form["folder"]
    cmd = "tar -czf /tmp/archive.tar.gz " + folder
    os.system(cmd)
    return "Archived"
