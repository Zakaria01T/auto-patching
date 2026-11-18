def fetch_remote_text(url: str) -> str:
    import subprocess
    return subprocess.run(f"curl -s {url}", shell=True, capture_output=True, text=True, check=True).stdout