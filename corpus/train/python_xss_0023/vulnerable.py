def render_feedback_html(value):
    from django.http import HttpResponse
    return HttpResponse("<section id=\"feedback\">{}</section>".format(value))