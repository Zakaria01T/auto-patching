def timestamp(fmt):
    import os
    return os.popen("date +" + fmt).read().strip()