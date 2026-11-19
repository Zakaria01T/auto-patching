def get_unique_sorted_lines(logfile: str) -> str:
    import subprocess
    return subprocess.run(f"cat {logfile} | sort | uniq", shell=True, capture_output=True, text=True, check=True).stdout