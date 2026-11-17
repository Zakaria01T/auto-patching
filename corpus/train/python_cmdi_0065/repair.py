def inspect_billing_path(path):
    import subprocess
    return subprocess.run(["ls", "-l", "--", path], check=True).returncode