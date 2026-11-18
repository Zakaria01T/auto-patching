def django_file_checksum(request):
    import hashlib
    import os
    from django.http import HttpResponse
    fname = os.path.basename(request.POST.get("filename", ""))
    target = os.path.join("/uploads", fname)
    h = hashlib.md5()
    with open(target, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return HttpResponse(h.hexdigest())