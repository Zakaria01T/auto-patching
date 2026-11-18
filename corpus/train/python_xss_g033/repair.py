def render_meetup_group(group_name):
    from flask import request
    from markupsafe import escape
    name = request.form.get('group', group_name)
    return "<h3 class='meetup'>{}</h3>".format(escape(name))
