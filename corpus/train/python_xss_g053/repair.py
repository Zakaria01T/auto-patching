def plant_tag():
    import html
    from flask import request
    plant = request.args.get("plant", "")
    return "<span class='plant'>{}</span>".format(html.escape(plant, quote=True))
