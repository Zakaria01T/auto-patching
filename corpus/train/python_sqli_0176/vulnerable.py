def lookup_summary_records(cursor, value):
    cursor.execute("SELECT id FROM summary WHERE owner = '" + value + "'")
    return cursor.fetchall()