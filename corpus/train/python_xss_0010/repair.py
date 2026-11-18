def render_post(text):
    import bleach
    import markdown
    html = markdown.markdown(text)
    return bleach.clean(html, tags=["p", "em", "strong", "ul", "ol", "li", "a"], strip=True)