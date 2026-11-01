import os


def backup_folder(folder):
    return os.system("tar -czf backup.tar.gz " + folder)
