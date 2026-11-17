def inspect_message_path(path):
    import os
    return os.popen("file " + path).read()