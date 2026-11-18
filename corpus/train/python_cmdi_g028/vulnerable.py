def disk_usage():
    import subprocess
    from flask import request
    mount = request.args.get("mount", "/")
    cmd = "df -h " + mount
    return subprocess.check_output(cmd, shell=True, text=True)
