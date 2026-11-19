def make_backup(folder):
    import tarfile
    with tarfile.open("backup.tgz", "w:gz") as tar:
        tar.add(folder)