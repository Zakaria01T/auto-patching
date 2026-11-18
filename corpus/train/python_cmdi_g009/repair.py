def fetch_url(request):
    import subprocess
    from django.http import HttpResponse
    url = request.GET.get("url", "https://example.com")
    output = subprocess.check_output(["curl", "-s", "--", url], text=True)
    return HttpResponse(output)
