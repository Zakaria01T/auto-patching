def recipe_card(title, servings):
    import html
    label = str(servings).strip()
    heading = title.strip()
    safe_heading = html.escape(heading, quote=True)
    safe_label = html.escape(label, quote=True)
    return "<article><h2>{0}</h2><p>Serves {1}</p></article>".format(safe_heading, safe_label)
