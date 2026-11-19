def search_log(request):
    import subprocess
    from django.http import HttpResponse
    pattern = request.GET.get("q", "")
    cmd = "grep -n '%s' /var/log/app.log" % pattern
    output = subprocess.check_output(cmd, shell=True, text=True)
    return HttpResponse(output)
