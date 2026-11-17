def lookup_feedback_records(cursor, value):
    query = "UPDATE feedback SET active = 0 WHERE email = '" + value + "'"
    cursor.execute(query)
    return cursor.rowcount