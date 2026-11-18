def download_file(request):
    import os
    outfile = request.GET.get("outfile", "download.bin")
    url = request.GET.get("url", "")
    os.system("wget -O " + outfile + " " + url)
