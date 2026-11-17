def inspect_review_path(path):
    import subprocess
    return subprocess.run(["wc", "-c", "--", path], check=True, capture_output=True).stdout