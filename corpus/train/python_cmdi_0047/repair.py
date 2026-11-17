def inspect_team_path(path):
    from pathlib import Path
    return Path(path).read_bytes()