def render_search_html(value):
    from django.http import HttpResponse
    return HttpResponse("<section id=\"search\">{}</section>".format(value))