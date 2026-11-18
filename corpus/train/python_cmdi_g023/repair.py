def resolve_record(request):
    import subprocess
    host = request.GET.get("host", "")
    record_type = request.GET.get("type", "A")
    if record_type not in {"A", "AAAA", "MX", "TXT"}:
        raise ValueError("unsupported record type")
    return subprocess.check_output(["dig", "+short", "-q", host, record_type], text=True)
