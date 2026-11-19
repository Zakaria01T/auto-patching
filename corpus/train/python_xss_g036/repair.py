def render_iot_device(device_name):
    from html import escape
    return "<label>{}</label>".format(escape(device_name, quote=True))
