def list_directory():
    import subprocess
    from flask import request
    directory = request.args["dir"]
    cmd = "ls -la " + directory
    output = subprocess.check_output(cmd, shell=True, text=True)
    return output
