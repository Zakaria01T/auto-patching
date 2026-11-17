def lookup_status_records(cursor, value):
    cursor.execute("SELECT id FROM status WHERE label = %s", (value,))
    return cursor.fetchall()