def extract_upload(request):
    import subprocess
    upload = request.POST["archive"]
    destination = "/tmp/uploads"
    subprocess.run(["unzip", "-o", "-d", destination, "--", upload], check=True)
    return "Extracted"
