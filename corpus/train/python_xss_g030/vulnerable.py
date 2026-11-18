def render_score_row(team_name):
    from flask import request
    name = request.args.get('team', team_name)
    return "<tr><td>" + name + "</td></tr>"
