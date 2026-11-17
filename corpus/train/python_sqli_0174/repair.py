def lookup_session_records(cursor, value):
    cursor.execute("DELETE FROM session WHERE token = %s", (value,))
    return cursor.rowcount