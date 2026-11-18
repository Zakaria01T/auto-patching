def generate_rental_receipt(car_model):
    from flask import request
    from markupsafe import escape
    model = request.args.get('model', car_model)
    return "<span class='car'>{}</span>".format(escape(model))
