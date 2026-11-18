def set_permissions():
    import subprocess
    from flask import request
    path = request.form["path"]
    subprocess.run(["chmod", "644", "--", path], check=True)
    return "Permissions set"
