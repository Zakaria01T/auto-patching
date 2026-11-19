def ensure_dir(name):
    import os
    os.makedirs(os.path.join("/srv/data", name), exist_ok=True)