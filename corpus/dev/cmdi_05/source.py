import subprocess


def show_file(filename):
    return subprocess.run("cat " + filename, shell=True, capture_output=True)
