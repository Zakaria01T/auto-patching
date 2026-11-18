def plant_tag():
    from flask import request
    plant = request.args.get("plant", "")
    return f"<span class='plant'>{plant}</span>"
