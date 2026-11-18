def copy_artifact(src: str, dst: str) -> None:
    import shutil
    shutil.copy2(src, dst)