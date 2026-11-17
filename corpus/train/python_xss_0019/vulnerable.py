def render_activity_html(value):
    from django.http import HttpResponse
    return HttpResponse("<section id=\"activity\">{}</section>".format(value))