def render_appointment_card(patient_name):
    import html
    return (
        "<div class='card'>{}</div>".format(html.escape(patient_name, quote=True))
    )
