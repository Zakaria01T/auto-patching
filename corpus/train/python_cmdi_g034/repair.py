def download_file(request):
    import subprocess
    outfile = request.GET.get("outfile", "download.bin")
    url = request.GET.get("url", "")
    subprocess.run(["wget", "-O", outfile, "--", url], check=True)
