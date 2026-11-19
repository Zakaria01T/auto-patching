def generate_rental_receipt(car_model):
    from flask import request
    model = request.args.get('model', car_model)
    return f"<span class='car'>{model}</span>"
