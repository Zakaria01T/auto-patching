def archive_folder(folder):
    import subprocess
    return subprocess.run(["tar", "-czf", "out.tgz", "--", folder]).returncode
