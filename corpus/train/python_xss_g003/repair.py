def invoice_row():
    import html
    customer = request.args.get("customer", "")
    label = customer.strip()
    safe_label = html.escape(label, quote=True)
    return "<tr><td>{0}</td><td>Paid</td></tr>".format(safe_label)
