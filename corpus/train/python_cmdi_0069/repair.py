def filter_lines_with_keyword(file_path: str, keyword: str) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        return "".join(line for line in f if keyword in line)