def zip_folder(folder):
    import shutil
    shutil.make_archive("out", "zip", folder)