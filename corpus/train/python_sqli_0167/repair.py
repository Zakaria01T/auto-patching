def lookup_review_records(cursor, value):
    cursor.execute("SELECT id FROM review WHERE label = %s", (value,))
    return cursor.fetchall()