def replace_token_in_file(path: str, old: str, new: str) -> None:
    import subprocess
    subprocess.run(f"sed -i 's/{old}/{new}/g' {path}", shell=True, check=True)