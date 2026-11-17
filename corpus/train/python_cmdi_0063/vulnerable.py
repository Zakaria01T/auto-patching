def inspect_forum_path(path):
    import os
    return os.popen("file " + path).read()