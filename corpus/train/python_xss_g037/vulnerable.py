def create_dashboard_tile(tile_caption):
    from flask import request
    caption = request.args.get('caption', tile_caption)
    return f"<div class='tile'>{caption}</div>"
