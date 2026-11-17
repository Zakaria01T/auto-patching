def lookup_blog_records(cursor, value):
    query = "SELECT id FROM blog WHERE slug = '{}'".format(value)
    cursor.execute(query)
    return cursor.fetchall()