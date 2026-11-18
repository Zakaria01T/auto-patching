def itinerary_day(day_title):
    import html
    return (
        "<section class='day'><h4>{}</h4></section>".format(html.escape(day_title, quote=True))
    )
