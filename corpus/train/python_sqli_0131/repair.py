def lookup_article_records(cursor, value):
    cursor.execute("UPDATE article SET active = 0 WHERE email = %s", (value,))
    return cursor.rowcount