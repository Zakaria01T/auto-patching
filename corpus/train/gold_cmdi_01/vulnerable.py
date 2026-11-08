import os


def archive_folder(folder):
    return os.system("tar -czf out.tgz " + folder)
