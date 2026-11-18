def embed_user_config(config: dict):
    from django.utils.html import json_script
    return json_script(config, "user-config")