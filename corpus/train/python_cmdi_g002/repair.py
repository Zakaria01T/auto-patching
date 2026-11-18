def archive_folder():
    import subprocess
    from flask import request
    folder = request.form["folder"]
    subprocess.run(["tar", "-czf", "/tmp/archive.tar.gz", "--", folder], check=True)
    return "Archived"
