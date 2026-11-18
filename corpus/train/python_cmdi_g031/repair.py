def inspect_container():
    import subprocess
    from flask import request
    name = request.args.get("name", "")
    subprocess.run(["docker", "inspect", "--", name], check=True)
