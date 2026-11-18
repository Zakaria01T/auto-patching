def build_listing_summary(listing_name):
    import html
    # Render a heading for a real estate listing.
    summary = "<h2>{}</h2>".format(html.escape(listing_name, quote=True))
    return summary
