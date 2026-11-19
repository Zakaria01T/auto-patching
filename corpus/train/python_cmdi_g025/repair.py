def verify_signature():
    import subprocess
    from flask import request
    signature = request.form["signature"]
    document = request.form["document"]
    subprocess.run(["gpg", "--verify", "--", signature, document], check=True)
