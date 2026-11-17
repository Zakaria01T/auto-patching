def inspect_settings_path(path):
    from pathlib import Path
    return Path(path).read_bytes()