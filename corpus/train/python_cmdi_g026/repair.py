def hash_file(path):
    import subprocess
    result = subprocess.run(["sha256sum", "--", path], capture_output=True, text=True, check=True)
    return result.stdout
