def folder_usage(folder):
    import subprocess
    subprocess.run(["du", "-sh", "--", folder], check=True)
    return "Done"
