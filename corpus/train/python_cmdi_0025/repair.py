def show_log(request):
    import os
    from django.http import HttpResponse
    base = os.path.realpath("/var/log/app")
    path = os.path.realpath(os.path.join(base, request.GET["name"]))
    if os.path.commonpath([base, path]) != base:
        raise ValueError("path outside log directory")
    with open(path) as fh:
        return HttpResponse(fh.read(), content_type="text/plain")