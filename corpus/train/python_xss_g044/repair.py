def ingredient_item(ingredient_name):
    import html
    # Build one entry in a recipe ingredient list.
    item = "<li>{}</li>".format(html.escape(ingredient_name, quote=True))
    return item
