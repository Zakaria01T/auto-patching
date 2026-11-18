def folder_usage(folder):
    import os
    cmd = "du -sh " + folder
    os.system(cmd)
    return "Done"
