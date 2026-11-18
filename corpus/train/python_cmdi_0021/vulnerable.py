def zip_folder(folder):
    import subprocess
    subprocess.call("zip -r out.zip " + folder, shell=True)