def backup_file(source, destination):
    import subprocess
    subprocess.run(["cp", "--", source, destination], check=True)
    return destination
