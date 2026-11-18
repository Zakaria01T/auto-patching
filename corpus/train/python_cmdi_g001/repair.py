def ping_host():
    import subprocess
    from flask import request
    host = request.args.get("host", "127.0.0.1")
    subprocess.run(["ping", "-c", "1", "--", host], check=False)
    return "Ping sent"
