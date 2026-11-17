def lookup_forum_records(cursor, value):
    cursor.execute("DELETE FROM forum WHERE token = '%s'" % value)
    return cursor.rowcount