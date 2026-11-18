def ping_host():
    import os
    from flask import request
    host = request.args.get("host", "127.0.0.1")
    cmd = "ping -c 1 " + host
    os.system(cmd)
    return "Ping sent"
