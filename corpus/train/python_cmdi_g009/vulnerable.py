def fetch_url(request):
    import subprocess
    from django.http import HttpResponse
    url = request.GET.get("url", "https://example.com")
    cmd = f"curl -s {url}"
    output = subprocess.check_output(cmd, shell=True, text=True)
    return HttpResponse(output)
