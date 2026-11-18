def tag_links(tags):
    from django.utils.html import format_html_join
    return format_html_join(", ", "<a href='/tag/{0}'>{0}</a>", ((t,) for t in tags))