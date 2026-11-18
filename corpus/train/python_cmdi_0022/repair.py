def replace_in_config(old, new):
    with open("config.txt") as fh:
        text = fh.read()
    with open("config.txt", "w") as fh:
        fh.write(text.replace(old, new))