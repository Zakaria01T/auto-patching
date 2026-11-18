def read_log_tail(request):
    import subprocess
    path = request.GET.get("path", "/var/log/syslog")
    lines = request.GET.get("lines", "100")
    cmd = "tail -n " + lines + " " + path
    return subprocess.check_output(cmd, shell=True, text=True)
