def convert_text():
    import subprocess
    from flask import request
    source = request.form["source"]
    target = request.form["target"]
    encoding = request.form["encoding"]
    if encoding not in {"utf-16", "latin-1", "ascii", "utf-8"}:
        raise ValueError("unsupported encoding")
    with open(target, "wb") as output:
        subprocess.run(["iconv", "-f", "utf-8", "-t", encoding, "--", source], stdout=output, check=True)
