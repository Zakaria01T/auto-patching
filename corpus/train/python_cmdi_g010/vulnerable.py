def check_certificate():
    import subprocess
    from flask import request
    path = request.args["cert"]
    cmd = "openssl x509 -in " + path + " -noout -subject"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout
