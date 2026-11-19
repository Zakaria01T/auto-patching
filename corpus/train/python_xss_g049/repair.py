def shift_item(volunteer_name):
    import html
    return (
        "<li class='shift'>{}</li>".format(html.escape(volunteer_name, quote=True))
    )
