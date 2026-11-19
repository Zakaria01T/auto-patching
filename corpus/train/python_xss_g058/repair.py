def result_bar():
    import html
    from flask import request
    option = request.args.get("option", "")
    return "<div class='bar'>{}</div>".format(html.escape(option, quote=True))
