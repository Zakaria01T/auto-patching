def find_files(pattern):
    import os
    return os.popen("find /srv/uploads -name " + pattern).read().splitlines()