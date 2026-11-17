def render_task_html(value):
    from html import escape
    return f"<li data-kind=\"task\">{escape(value, quote=True)}</li>"