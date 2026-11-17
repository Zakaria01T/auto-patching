def lookup_billing_records(cursor, value):
    cursor.execute("SELECT id FROM billing WHERE owner = '" + value + "'")
    return cursor.fetchall()