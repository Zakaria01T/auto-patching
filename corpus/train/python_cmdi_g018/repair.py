def sync_folder(request):
    import subprocess
    source = request.POST.get("source", "")
    target = request.POST.get("target", "")
    subprocess.run(["rsync", "-a", "--", source + "/", target + "/"], check=True)
