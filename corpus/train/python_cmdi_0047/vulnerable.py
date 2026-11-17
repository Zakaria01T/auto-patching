def inspect_team_path(path):
    import subprocess
    return subprocess.check_output("cat " + path, shell=True)