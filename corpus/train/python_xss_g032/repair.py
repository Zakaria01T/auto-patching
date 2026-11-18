def create_tracking_line(carrier_name):
    from html import escape
    return "<div class='tracking'>{}</div>".format(escape(carrier_name, quote=True))
