def print_document():
    import subprocess
    from flask import request
    printer = request.form["printer"]
    filename = request.form["filename"]
    subprocess.run(["lpr", "-P", printer, "--", filename], check=True)
