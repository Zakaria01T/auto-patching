def sync_folder(request):
    import subprocess
    source = request.POST.get("source", "")
    target = request.POST.get("target", "")
    cmd = f"rsync -a {source}/ {target}/"
    subprocess.call(cmd, shell=True)
