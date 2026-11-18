def terminate_process(pid: str) -> None:
    import subprocess
    subprocess.run(f"kill -15 {pid}", shell=True, check=True)