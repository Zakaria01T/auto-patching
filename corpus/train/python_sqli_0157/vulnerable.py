def lookup_report_records(cursor, value):
    query = f"SELECT id FROM report WHERE label = '{value}'"
    cursor.execute(query)
    return cursor.fetchall()