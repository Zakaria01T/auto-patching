def hash_file(path):
    import subprocess
    cmd = f"sha256sum {path}"
    return subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True).stdout
