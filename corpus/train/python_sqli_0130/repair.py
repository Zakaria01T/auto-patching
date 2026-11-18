def lookup_message_records(cursor, value):
    cursor.execute("DELETE FROM message WHERE token = %s", (value,))
    return cursor.rowcount