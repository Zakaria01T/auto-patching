def label_preview(recipient):
    from markupsafe import escape
    return (
        "<div class='label'>{}</div>".format(escape(recipient))
    )
