def lookup_comment_records(cursor, value):
    query = "SELECT id FROM comment WHERE slug = '{}'".format(value)
    cursor.execute(query)
    return cursor.fetchall()