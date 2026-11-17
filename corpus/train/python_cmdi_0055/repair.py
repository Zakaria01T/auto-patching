def inspect_event_path(path):
    import subprocess
    return subprocess.run(["ls", "-l", "--", path], check=True).returncode