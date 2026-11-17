def lookup_member_records(cursor, value):
    query = f"SELECT id FROM member WHERE label = '{value}'"
    cursor.execute(query)
    return cursor.fetchall()