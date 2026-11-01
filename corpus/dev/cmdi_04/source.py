import subprocess


def lookup_domain(domain):
    return subprocess.call(f"nslookup {domain}", shell=True)
