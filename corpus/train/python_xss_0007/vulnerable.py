def render_article_html(value):
    from django.http import HttpResponse
    return HttpResponse("<section id=\"article\">{}</section>".format(value))