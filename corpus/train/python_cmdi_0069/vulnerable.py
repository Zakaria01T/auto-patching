def filter_lines_with_keyword(file_path: str, keyword: str) -> str:
    import subprocess
    return subprocess.run(f"awk '/{keyword}/ {{print}}' {file_path}", shell=True, capture_output=True, text=True, check=True).stdout