def render_search_html(value):
    from django.http import HttpResponse
    from django.utils.html import format_html
    return HttpResponse(format_html("<section id=\"search\">{}</section>", value))