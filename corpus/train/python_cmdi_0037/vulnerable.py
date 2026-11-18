def append_audit_entry(logfile: str, message: str) -> None:
    import os
    os.system(f"echo {message} >> {logfile}")