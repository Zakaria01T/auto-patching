def key_fingerprint(key_path):
    import subprocess
    fingerprint = subprocess.check_output(["ssh-keygen", "-lf", "--", key_path], text=True)
    return fingerprint
