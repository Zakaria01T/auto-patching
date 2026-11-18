def django_file_checksum(request):
    import subprocess
    from django.http import HttpResponse
    fname = request.POST.get("filename", "")
    out = subprocess.check_output(f"md5sum /uploads/{fname}", shell=True, text=True)
    return HttpResponse(out)