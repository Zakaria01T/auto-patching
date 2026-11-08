def welcome(name):
    import html
    return "<h1>Welcome {}</h1>".format(html.escape(name))
