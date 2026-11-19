def disk_usage():
    import subprocess
    from flask import request
    mount = request.args.get("mount", "/")
    return subprocess.check_output(["df", "-h", "--", mount], text=True)
