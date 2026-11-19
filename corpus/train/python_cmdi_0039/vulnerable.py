def count_file_lines(path: str) -> str:
    import os
    return os.popen("wc -l " + path).read()