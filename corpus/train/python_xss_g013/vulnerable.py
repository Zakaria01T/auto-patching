def book_entry(title, author):
    name = title.strip()
    writer = author.strip()
    return f"<li><b>{name}</b> by {writer}</li>"
