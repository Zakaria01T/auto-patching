def free_space(mount):
    import shutil
    return shutil.disk_usage(mount).free