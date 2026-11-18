def render_custom_header(title: str) -> str:
    from jinja2 import Environment
    env = Environment(autoescape=True)
    return env.from_string("<header><h1>{{ title }}</h1></header>").render(title=title)