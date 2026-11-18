def flight_status(flight, status):
    code = flight.strip().upper()
    state = status.strip()
    return f"<div class='flight'><b>{code}</b> is {state}</div>"
