import subprocess


def first_lines(filename):
    return subprocess.check_output(f"head -n 2 {filename}", shell=True)
