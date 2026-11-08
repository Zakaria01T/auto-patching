def first_lines(filename):
    import subprocess
    return subprocess.check_output(["head", "-n", "2", "--", filename])
