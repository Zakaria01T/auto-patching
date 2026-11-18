def print_document():
    import os
    from flask import request
    printer = request.form["printer"]
    filename = request.form["filename"]
    cmd = "lpr -P {} {}".format(printer, filename)
    os.system(cmd)
