def lookup_order_records(cursor, value):
    cursor.execute("UPDATE order SET active = 0 WHERE email = %s", (value,))
    return cursor.rowcount