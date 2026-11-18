def extract_upload(archive, dest):
    import zipfile
    with zipfile.ZipFile(archive) as zf:
        zf.extractall(dest)