def search_log(request):
    import subprocess
    from django.http import HttpResponse
    pattern = request.GET.get("q", "")
    output = subprocess.check_output(["grep", "-n", "--", pattern, "/var/log/app.log"], text=True)
    return HttpResponse(output)
