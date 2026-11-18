def count_lines():
    import subprocess
    from flask import request
    filename = request.args["file"]
    cmd = "wc -l " + filename
    output = subprocess.check_output(cmd, shell=True, text=True)
    return output
