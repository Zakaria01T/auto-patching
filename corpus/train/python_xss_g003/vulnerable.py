def invoice_row():
    customer = request.args.get("customer", "")
    label = customer.strip()
    return "<tr><td>" + label + "</td><td>Paid</td></tr>"
