import subprocess


def search_log(pattern):
    return subprocess.check_output("grep " + pattern + " app.log", shell=True)
