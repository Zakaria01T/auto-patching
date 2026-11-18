def display_bug_comment(comment_text):
    from flask import request
    text = request.form.get('comment', comment_text)
    return f"<p class='bug-comment'>{text}</p>"
