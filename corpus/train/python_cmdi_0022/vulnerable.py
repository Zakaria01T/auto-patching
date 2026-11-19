def replace_in_config(old, new):
    import os
    os.system("sed -i 's/%s/%s/g' config.txt" % (old, new))