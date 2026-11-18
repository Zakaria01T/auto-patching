def photo_caption():
    from flask import request
    caption = request.form.get("caption", "")
    return f"<figcaption>{caption}</figcaption>"
