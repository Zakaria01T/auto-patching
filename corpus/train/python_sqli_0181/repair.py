def lookup_billing_records(cursor, value):
    cursor.execute("SELECT id FROM billing WHERE owner = %s", (value,))
    return cursor.fetchall()