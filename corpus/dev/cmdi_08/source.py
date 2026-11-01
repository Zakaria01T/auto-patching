import os


def folder_size(path):
    return os.popen("du -sh " + path).read()
