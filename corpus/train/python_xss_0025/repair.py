def django_greeting_view(request):
    from django.http import HttpResponse
    from django.utils.html import format_html
    name = request.GET.get("name", "Guest")
    return HttpResponse(format_html("<p>Hello, {}</p>", name))