def render_invoice_line(item_name: str) -> str:
    from jinja2 import Template
    tpl = Template("<li>{{ item }}</li>", autoescape=True)
    return tpl.render(item=item_name)