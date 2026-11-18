def recipe_card(title, servings):
    label = str(servings).strip()
    heading = title.strip()
    return f"<article><h2>{heading}</h2><p>Serves {label}</p></article>"
