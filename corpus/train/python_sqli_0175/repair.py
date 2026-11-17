def lookup_feedback_records(cursor, value):
    cursor.execute("UPDATE feedback SET active = 0 WHERE email = %s", (value,))
    return cursor.rowcount