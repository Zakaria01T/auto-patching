def count_file_lines(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        count = sum(1 for _ in f)
    return f"{count} {path}\n"