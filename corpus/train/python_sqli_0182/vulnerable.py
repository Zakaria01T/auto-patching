def lookup_status_records(cursor, value):
    query = f"SELECT id FROM status WHERE label = '{value}'"
    cursor.execute(query)
    return cursor.fetchall()