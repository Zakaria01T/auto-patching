def django_greeting_view(request):
    from django.http import HttpResponse
    name = request.GET.get("name", "Guest")
    return HttpResponse(f"<p>Hello, {name}</p>")