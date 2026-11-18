def terminate_process(pid: str) -> None:
    import os
    import signal
    pid_num = int(pid)
    if pid_num <= 0:
        raise ValueError("Invalid PID")
    os.kill(pid_num, signal.SIGTERM)