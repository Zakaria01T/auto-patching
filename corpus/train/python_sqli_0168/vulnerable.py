def lookup_support_records(cursor, value):
    query = "SELECT id FROM support WHERE slug = '{}'".format(value)
    cursor.execute(query)
    return cursor.fetchall()