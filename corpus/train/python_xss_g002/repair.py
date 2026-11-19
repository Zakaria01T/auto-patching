def product_card(name, price):
    import html
    price_text = str(price)
    safe_name = html.escape(name, quote=True)
    safe_price = html.escape(price_text, quote=True)
    card = "<div class='product'><h3>{0}</h3><span>{1}</span></div>".format(safe_name, safe_price)
    return card
