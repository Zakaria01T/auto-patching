def greeting(request):
    from django.http import HttpResponse
    return HttpResponse("<b>Welcome, %s</b>" % request.GET.get("user"))