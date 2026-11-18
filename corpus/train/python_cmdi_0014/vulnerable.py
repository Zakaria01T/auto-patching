def free_space(mount):
    import os
    return os.popen("df -h " + mount).read()