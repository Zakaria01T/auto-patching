def set_permissions():
    import os
    from flask import request
    path = request.form["path"]
    cmd = "chmod 644 " + path
    os.system(cmd)
    return "Permissions set"
