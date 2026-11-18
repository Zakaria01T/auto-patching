def make_backup(folder):
    import subprocess
    subprocess.call("tar czf backup.tgz " + folder, shell=True)