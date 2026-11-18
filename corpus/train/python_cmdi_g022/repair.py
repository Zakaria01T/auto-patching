def scan_host(host):
    import subprocess
    output = subprocess.check_output(["nmap", "-sV", "--", host], text=True)
    return output
