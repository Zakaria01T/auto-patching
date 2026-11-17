def lookup_activity_records(cursor, value):
    cursor.execute("UPDATE activity SET active = 0 WHERE email = %s", (value,))
    return cursor.rowcount