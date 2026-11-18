def change_file_owner(owner: str, target: str) -> None:
    import shutil
    shutil.chown(target, user=owner)