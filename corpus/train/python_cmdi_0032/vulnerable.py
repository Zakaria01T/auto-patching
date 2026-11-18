def ensure_directory(dir_path: str) -> None:
    import os
    os.system("mkdir -p %s" % dir_path)