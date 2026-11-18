def scan_host(host):
    import subprocess
    cmd = "nmap -sV " + host
    return subprocess.check_output(cmd, shell=True, text=True)
