def last_lines(n):
    from collections import deque
    with open("/var/log/app.log") as fh:
        return "".join(deque(fh, maxlen=int(n)))