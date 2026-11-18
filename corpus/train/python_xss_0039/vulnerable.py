def render_django_fragment(username: str) -> str:
    from django.template import Context, Engine
    engine = Engine(autoescape=False)
    tpl = engine.from_string("<p>{{ user }}</p>")
    return tpl.render(Context({"user": username}))