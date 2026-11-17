def lookup_blog_records(cursor, value):
    cursor.execute("SELECT id FROM blog WHERE slug = %s", (value,))
    return cursor.fetchall()