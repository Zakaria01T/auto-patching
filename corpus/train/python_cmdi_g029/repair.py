def list_crontab(user):
    import subprocess
    listing = subprocess.check_output(["crontab", "-l", "-u", user], text=True)
    return listing
