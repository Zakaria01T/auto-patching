def greeting(request):
    from django.http import HttpResponse
    from django.utils.html import format_html
    return HttpResponse(format_html("<b>Welcome, {}</b>", request.GET.get("user")))