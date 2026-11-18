def list_crontab(user):
    import subprocess
    cmd = "crontab -l -u " + user
    return subprocess.check_output(cmd, shell=True, text=True)
