def lookup_report_records(cursor, value):
    cursor.execute("SELECT id FROM report WHERE label = %s", (value,))
    return cursor.fetchall()