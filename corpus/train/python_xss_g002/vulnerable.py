def product_card(name, price):
    price_text = str(price)
    card = f"<div class='product'><h3>{name}</h3><span>{price_text}</span></div>"
    return card
