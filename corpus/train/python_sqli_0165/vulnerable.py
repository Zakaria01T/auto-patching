def lookup_order_records(cursor, value):
    query = "UPDATE order SET active = 0 WHERE email = '" + value + "'"
    cursor.execute(query)
    return cursor.rowcount