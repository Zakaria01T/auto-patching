def create_pet_profile(pet_name):
    from html import escape
    return "<h2>{}</h2>".format(escape(pet_name, quote=True))
