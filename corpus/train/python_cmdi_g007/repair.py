def count_lines():
    import subprocess
    from flask import request
    filename = request.args["file"]
    output = subprocess.check_output(["wc", "-l", "--", filename], text=True)
    return output
