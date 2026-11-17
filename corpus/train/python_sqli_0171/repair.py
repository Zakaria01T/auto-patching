def lookup_event_records(cursor, value):
    cursor.execute("SELECT id FROM event WHERE owner = %s", (value,))
    return cursor.fetchall()