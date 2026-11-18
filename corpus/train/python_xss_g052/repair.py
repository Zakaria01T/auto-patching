def field_label(field_name):
    import html
    return (
        "<label>{}</label>".format(html.escape(field_name, quote=True))
    )
