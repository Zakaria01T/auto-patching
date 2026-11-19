def key_fingerprint(key_path):
    import subprocess
    cmd = "ssh-keygen -lf " + key_path
    return subprocess.check_output(cmd, shell=True, text=True)
