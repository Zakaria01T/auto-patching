def replace_token_in_file(path: str, old: str, new: str) -> None:
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.replace(old, new))