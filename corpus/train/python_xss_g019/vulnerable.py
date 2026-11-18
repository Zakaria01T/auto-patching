def wiki_title():
    title = request.args.get("title", "")
    text = title.strip()
    markup = "<h1 class='wiki'>" + text + "</h1>"
    return markup
