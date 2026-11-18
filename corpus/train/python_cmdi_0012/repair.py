def lock_key(keyfile):
    import os
    os.chmod(keyfile, 0o600)