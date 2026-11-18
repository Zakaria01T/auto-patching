def stats_block(data):
    from django.utils.html import json_script
    return json_script(data, "stats")