def extract_upload(archive, dest):
    import os
    os.system(f"unzip -o {archive} -d {dest}")