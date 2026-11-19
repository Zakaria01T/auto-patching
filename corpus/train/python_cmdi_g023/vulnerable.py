def resolve_record(request):
    import subprocess
    host = request.GET.get("host", "")
    record_type = request.GET.get("type", "A")
    cmd = "dig +short %s %s" % (host, record_type)
    return subprocess.check_output(cmd, shell=True, text=True)
