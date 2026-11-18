def render_score_row(team_name):
    from flask import request
    from markupsafe import escape
    name = request.args.get('team', team_name)
    return "<tr><td>{}</td></tr>".format(escape(name))
