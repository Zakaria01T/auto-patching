def lookup_support_records(cursor, value):
    cursor.execute("SELECT id FROM support WHERE slug = %s", (value,))
    return cursor.fetchall()