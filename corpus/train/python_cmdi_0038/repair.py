def inspect_message_path(path):
    import subprocess
    return subprocess.check_output(["file", "--", path], text=True)