def inspect_dashboard_path(path):
    import subprocess
    return subprocess.check_output(["file", "--", path], text=True)