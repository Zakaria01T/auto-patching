def display_review_stars(product_name):
    import html
    return "<span class='stars'>{}</span>".format(html.escape(product_name, quote=True))
