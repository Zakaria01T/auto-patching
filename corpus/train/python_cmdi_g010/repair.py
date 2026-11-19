def check_certificate():
    import subprocess
    from flask import request
    path = request.args["cert"]
    result = subprocess.run(["openssl", "x509", "-in", path, "-noout", "-subject"], capture_output=True, text=True)
    return result.stdout
