def convert_text():
    import subprocess
    from flask import request
    source = request.form["source"]
    target = request.form["target"]
    encoding = request.form["encoding"]
    cmd = "iconv -f utf-8 -t {} {} > {}".format(encoding, source, target)
    subprocess.run(cmd, shell=True, check=True)
