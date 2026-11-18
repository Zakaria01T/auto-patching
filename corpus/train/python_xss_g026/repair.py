def list_survey_answers(answer):
    import html
    return "<li>{}</li>".format(html.escape(answer, quote=True))
