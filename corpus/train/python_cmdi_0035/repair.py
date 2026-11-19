def set_readonly_perms(filename: str) -> None:
    import os
    os.chmod(filename, 0o444)