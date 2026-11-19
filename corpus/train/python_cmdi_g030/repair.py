def service_status(request):
    import subprocess
    service = request.POST.get("service", "")
    return subprocess.run(["systemctl", "status", "--", service], capture_output=True, text=True)
