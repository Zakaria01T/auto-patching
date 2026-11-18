def read_config_via_bash(path: str) -> str:
    import subprocess
    return subprocess.check_output(["bash", "-c", "cat " + path], text=True)