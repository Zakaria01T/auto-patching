def change_file_owner(owner: str, target: str) -> None:
    import subprocess
    subprocess.run(f"chown {owner} {target}", shell=True, check=True)