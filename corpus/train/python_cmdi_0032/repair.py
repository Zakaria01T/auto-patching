def ensure_directory(dir_path: str) -> None:
    import os
    os.makedirs(dir_path, exist_ok=True)