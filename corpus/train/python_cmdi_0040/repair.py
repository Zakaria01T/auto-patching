def inspect_ticket_path(path):
    import subprocess
    return subprocess.run(["ls", "-l", "--", path], check=True).returncode