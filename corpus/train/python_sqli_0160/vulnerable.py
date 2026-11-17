def lookup_search_records(cursor, value):
    query = "UPDATE search SET active = 0 WHERE email = '" + value + "'"
    cursor.execute(query)
    return cursor.rowcount