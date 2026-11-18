def stats_block(data):
    import json
    from django.utils.safestring import mark_safe
    return mark_safe("<script>window.stats = " + json.dumps(data) + ";</script>")