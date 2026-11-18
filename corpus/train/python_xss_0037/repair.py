def prepare_flash_alert(raw_alert: str):
    from markupsafe import escape
    return escape(raw_alert)