def rename_file(old, new):
    import os
    os.system("mv {} {}".format(old, new))