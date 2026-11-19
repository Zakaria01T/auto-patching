def trace_host(host):
    import subprocess
    cmd = "traceroute " + host
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, text=True)
    return process.communicate()[0]
