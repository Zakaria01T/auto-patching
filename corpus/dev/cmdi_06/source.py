import os


def remove_file(filename):
    return os.system(f"rm -f {filename}")
