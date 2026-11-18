def file_size(path):
    import os
    return os.stat(path).st_size