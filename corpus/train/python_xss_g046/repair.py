def package_heading(package_name):
    import html
    return (
        "<h1>{}</h1>".format(html.escape(package_name, quote=True))
    )
