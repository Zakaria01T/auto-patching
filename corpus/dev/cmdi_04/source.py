import subprocess


def count_lines(filename):
    return subprocess.check_output(f"wc -l {filename}", shell=True)
