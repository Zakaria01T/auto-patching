def lookup_activity_records(cursor, value):
    query = "UPDATE activity SET active = 0 WHERE email = '" + value + "'"
    cursor.execute(query)
    return cursor.rowcount