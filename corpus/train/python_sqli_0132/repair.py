def lookup_invoice_records(cursor, value):
    cursor.execute("SELECT id FROM invoice WHERE slug = %s", (value,))
    return cursor.fetchall()