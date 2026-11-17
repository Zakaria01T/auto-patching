def lookup_customer_records(cursor, value):
    cursor.execute("DELETE FROM customer WHERE token = '%s'" % value)
    return cursor.rowcount