def photo_caption():
    import html
    from flask import request
    caption = request.form.get("caption", "")
    return "<figcaption>{}</figcaption>".format(html.escape(caption, quote=True))
