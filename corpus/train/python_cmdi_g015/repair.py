def list_directory():
    import subprocess
    from flask import request
    directory = request.args["dir"]
    output = subprocess.check_output(["ls", "-la", "--", directory], text=True)
    return output
