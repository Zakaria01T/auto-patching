import subprocess


def search_log(pattern):
    return subprocess.Popen("grep " + pattern + " app.log", shell=True)
