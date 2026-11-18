def list_folder(folder):
    import subprocess
    return subprocess.getoutput("ls " + folder).splitlines()