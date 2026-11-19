def chat_line(sender, text):
    name = sender.strip()
    body = text.strip()
    return f"<p><strong>{name}</strong>: {body}</p>"
