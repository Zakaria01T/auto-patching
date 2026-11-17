def lookup_member_records(cursor, value):
    cursor.execute("SELECT id FROM member WHERE label = %s", (value,))
    return cursor.fetchall()