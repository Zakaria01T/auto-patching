def append_audit_entry(logfile: str, message: str) -> None:
    with open(logfile, "a", encoding="utf-8") as f:
        f.write(message + "\n")