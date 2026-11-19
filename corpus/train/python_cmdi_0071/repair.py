def get_unique_sorted_lines(logfile: str) -> str:
    with open(logfile, "r", encoding="utf-8") as f:
        return "".join(sorted(set(f)))