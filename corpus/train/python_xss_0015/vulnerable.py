def render_order_html(value):
    from django.http import HttpResponse
    return HttpResponse("<section id=\"order\">{}</section>".format(value))