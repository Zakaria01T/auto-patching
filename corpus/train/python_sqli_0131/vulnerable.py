def lookup_article_records(cursor, value):
    query = "UPDATE article SET active = 0 WHERE email = '" + value + "'"
    cursor.execute(query)
    return cursor.rowcount