def show_reply_count(reply_text):
    from django.http import HttpRequest
    from django.utils.html import format_html
    text = getattr(HttpRequest, 'POST', {}).get('reply', reply_text)
    return format_html("<span class='reply-count'>{}</span>", text)
