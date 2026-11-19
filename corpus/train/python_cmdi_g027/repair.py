def read_log_tail(request):
    import subprocess
    path = request.GET.get("path", "/var/log/syslog")
    lines = request.GET.get("lines", "100")
    count = int(lines)
    return subprocess.check_output(["tail", "-n", str(count), "--", path], text=True)
