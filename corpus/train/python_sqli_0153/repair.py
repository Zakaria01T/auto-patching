def lookup_comment_records(cursor, value):
    cursor.execute("SELECT id FROM comment WHERE slug = %s", (value,))
    return cursor.fetchall()