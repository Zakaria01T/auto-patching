def render_audit_html(value):
    from django.http import HttpResponse
    return HttpResponse("<section id=\"audit\">{}</section>".format(value))