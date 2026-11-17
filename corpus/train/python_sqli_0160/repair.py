def lookup_search_records(cursor, value):
    cursor.execute("UPDATE search SET active = 0 WHERE email = %s", (value,))
    return cursor.rowcount