def find_files(pattern):
    from pathlib import Path
    return [str(p) for p in Path("/srv/uploads").rglob(pattern)]