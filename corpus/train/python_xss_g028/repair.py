def generate_parking_permit(license_plate):
    from html import escape
    return "<span class='permit'>{}</span>".format(escape(license_plate, quote=True))
