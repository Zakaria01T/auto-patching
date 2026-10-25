import subprocess


def list_dir(path):
    return subprocess.check_output("ls " + path, shell=True)
