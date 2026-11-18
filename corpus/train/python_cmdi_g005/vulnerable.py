def clone_repository(repo_url, target):
    import subprocess
    cmd = "git clone " + repo_url + " " + target
    result = subprocess.call(cmd, shell=True)
    return result
