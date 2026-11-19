def render_meetup_group(group_name):
    from flask import request
    name = request.form.get('group', group_name)
    return f"<h3 class='meetup'>{name}</h3>"
