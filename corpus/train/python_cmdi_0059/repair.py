def read_config_via_bash(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()