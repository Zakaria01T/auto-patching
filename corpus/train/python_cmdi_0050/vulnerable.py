def compute_file_sha256(filepath: str) -> str:
    import subprocess
    return subprocess.run(f"openssl dgst -sha256 {filepath}", shell=True, capture_output=True, text=True, check=True).stdout