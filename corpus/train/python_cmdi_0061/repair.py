def inspect_catalog_path(path):
    import subprocess
    return subprocess.run(["wc", "-c", "--", path], check=True, capture_output=True).stdout