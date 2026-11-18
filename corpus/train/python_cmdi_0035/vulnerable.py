def set_readonly_perms(filename: str) -> None:
    import os
    os.system("chmod 444 " + filename)