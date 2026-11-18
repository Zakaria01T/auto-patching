def backup_file(source, destination):
    import os
    cmd = "cp " + source + " " + destination
    os.system(cmd)
    return destination
