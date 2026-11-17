def lookup_invoice_records(cursor, value):
    query = "SELECT id FROM invoice WHERE slug = '{}'".format(value)
    cursor.execute(query)
    return cursor.fetchall()