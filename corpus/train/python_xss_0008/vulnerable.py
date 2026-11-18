def make_env():
    import jinja2
    return jinja2.Environment(loader=jinja2.FileSystemLoader("templates"), autoescape=False)