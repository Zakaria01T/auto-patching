def stop_worker(pid):
    import os
    import signal
    os.kill(int(pid), signal.SIGKILL)