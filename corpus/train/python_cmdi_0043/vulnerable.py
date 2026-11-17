def inspect_dashboard_path(path):
    import os
    return os.popen("file " + path).read()