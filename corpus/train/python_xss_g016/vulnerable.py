def weather_widget():
    icon = request.args.get("icon", "")
    icon = icon.strip()
    return f"<div class='weather'><img src='{icon}' alt='weather'></div>"
