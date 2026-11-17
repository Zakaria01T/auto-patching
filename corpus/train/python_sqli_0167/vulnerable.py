def lookup_review_records(cursor, value):
    query = f"SELECT id FROM review WHERE label = '{value}'"
    cursor.execute(query)
    return cursor.fetchall()