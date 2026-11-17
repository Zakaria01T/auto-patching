def inspect_member_path(path):
    import subprocess
    return subprocess.run(f"wc -c {path}", shell=True, capture_output=True).stdout