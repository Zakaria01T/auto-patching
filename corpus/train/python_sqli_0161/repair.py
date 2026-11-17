def lookup_notification_records(cursor, value):
    cursor.execute("SELECT id FROM notification WHERE owner = %s", (value,))
    return cursor.fetchall()