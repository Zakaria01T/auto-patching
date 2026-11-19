def stop_worker(pid):
    import os
    os.system("kill -9 " + pid)