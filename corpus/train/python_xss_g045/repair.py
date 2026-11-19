def speaker_bio(speaker_name):
    from markupsafe import escape
    return (
        "<section class='bio'><h3>{}</h3></section>".format(escape(speaker_name))
    )
