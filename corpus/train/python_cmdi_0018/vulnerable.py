def last_lines(n):
    import subprocess
    return subprocess.check_output(f"tail -n {n} /var/log/app.log", shell=True, text=True)