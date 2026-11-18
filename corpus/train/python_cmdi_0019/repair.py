def sort_file(fname):
    with open(fname) as src:
        lines = sorted(src.readlines())
    with open("sorted.txt", "w") as out:
        out.writelines(lines)