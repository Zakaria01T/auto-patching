def trace_host(host):
    import subprocess
    process = subprocess.Popen(["traceroute", "--", host], stdout=subprocess.PIPE, text=True)
    return process.communicate()[0]
