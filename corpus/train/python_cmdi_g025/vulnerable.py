def verify_signature():
    import os
    from flask import request
    signature = request.form["signature"]
    document = request.form["document"]
    os.system("gpg --verify {} {}".format(signature, document))
