def inspect_customer_path(path):
    import os
    return os.popen("file " + path).read()