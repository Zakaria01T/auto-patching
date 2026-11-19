def create_dashboard_tile(tile_caption):
    from flask import request
    from markupsafe import escape
    caption = request.args.get('caption', tile_caption)
    return "<div class='tile'>{}</div>".format(escape(caption))
