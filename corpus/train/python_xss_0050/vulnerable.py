def build_tag_list(tags: list[str]) -> str:
    items = "".join(f"<li>{t}</li>" for t in tags)
    return f"<ul>{items}</ul>"