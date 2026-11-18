def prepare_flash_alert(raw_alert: str):
    from markupsafe import Markup
    return Markup(raw_alert)