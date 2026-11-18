def create_exhibit_label(artifact_name):
    import html
    return "<figcaption>{}</figcaption>".format(html.escape(artifact_name, quote=True))
