def inspect_order_path(path):
    import subprocess
    command = "sha256sum " + path
    return subprocess.check_output(command, shell=True, text=True)