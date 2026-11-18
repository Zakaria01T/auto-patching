def result_bar():
    from flask import request
    option = request.args.get("option", "")
    return "<div class='bar'>" + option + "</div>"
