def inspect_container():
    import os
    from flask import request
    name = request.args.get("name", "")
    os.system("docker inspect " + name)
