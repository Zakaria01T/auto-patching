def embed_user_config(config: dict):
    import json
    from django.utils.safestring import mark_safe
    return mark_safe(f"<script>window.CFG = {json.dumps(config)};</script>")