def delete_temp_file(filepath: str) -> None:
    import os
    if os.path.exists(filepath):
        os.remove(filepath)