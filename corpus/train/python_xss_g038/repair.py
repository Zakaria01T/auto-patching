def preview_newsletter(subject_line):
    import html
    return "<p class='preview'>{}</p>".format(html.escape(subject_line, quote=True))
