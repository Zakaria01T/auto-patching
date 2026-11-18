def file_md5(path):
    import os
    return os.popen("md5sum " + path).read().split()[0]