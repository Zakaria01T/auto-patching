def render_booking_summary(hotel_name):
    from html import escape
    return "<div class='booking'>{}</div>".format(escape(hotel_name, quote=True))
