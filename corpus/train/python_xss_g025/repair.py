def display_bug_comment(comment_text):
    from flask import request
    from markupsafe import escape
    text = request.form.get('comment', comment_text)
    return "<p class='bug-comment'>{}</p>".format(escape(text))
