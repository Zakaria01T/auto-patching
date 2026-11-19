def resize_image():
    import os
    from flask import request
    size = request.args.get("size", "800x600")
    path = request.args.get("path", "")
    os.system("mogrify -resize " + size + " " + path)
