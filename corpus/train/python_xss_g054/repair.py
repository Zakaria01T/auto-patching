def notice_banner(message):
    import html
    return (
        "<div class='notice'>{}</div>".format(html.escape(message, quote=True))
    )
