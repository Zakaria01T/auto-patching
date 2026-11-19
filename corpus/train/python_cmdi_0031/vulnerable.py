def delete_temp_file(filepath: str) -> None:
    import os
    os.system("rm -f " + filepath)