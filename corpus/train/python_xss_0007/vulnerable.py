def tag_links(tags):
    from django.utils.safestring import mark_safe
    return mark_safe(", ".join("<a href='/tag/%s'>%s</a>" % (t, t) for t in tags))