def extract_upload(request):
    import os
    upload = request.POST["archive"]
    destination = "/tmp/uploads"
    cmd = "unzip -o %s -d %s" % (upload, destination)
    os.system(cmd)
    return "Extracted"
