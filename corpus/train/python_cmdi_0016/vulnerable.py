def count_lines(fname):
    import os
    return int(os.popen("wc -l < " + fname).read())