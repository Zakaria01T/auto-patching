def show_reply_count(reply_text):
    from django.http import HttpRequest
    text = getattr(HttpRequest, 'POST', {}).get('reply', reply_text)
    return f"<span class='reply-count'>{text}</span>"
