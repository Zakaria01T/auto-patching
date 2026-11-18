def service_status(request):
    import subprocess
    service = request.POST.get("service", "")
    cmd = "systemctl status " + service
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)
