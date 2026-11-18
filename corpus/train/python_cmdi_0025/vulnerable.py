def show_log(request):
    import os
    from django.http import HttpResponse
    return HttpResponse(os.popen("cat /var/log/app/" + request.GET["name"]).read(), content_type="text/plain")