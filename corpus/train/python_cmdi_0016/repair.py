def count_lines(fname):
    with open(fname, "rb") as fh:
        return sum(1 for _ in fh)