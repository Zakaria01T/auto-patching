def inspect_comment_path(path):
    import subprocess
    return subprocess.check_output("cat " + path, shell=True)