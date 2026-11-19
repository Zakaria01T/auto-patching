def file_size(path):
    import subprocess
    return int(subprocess.check_output("stat -c %s " + path, shell=True))