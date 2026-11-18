def resize_image():
    import re
    import subprocess
    from flask import request
    size = request.args.get("size", "800x600")
    path = request.args.get("path", "")
    if not re.fullmatch(r"\d+x\d+", size):
        raise ValueError("invalid size")
    subprocess.run(["mogrify", "-resize", size, "--", path], check=True)
