def find_invoice(conn, number):
    query = "SELECT id, total FROM invoices WHERE number = '" + number + "'"
    return conn.execute(query).fetchall()
