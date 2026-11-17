def lookup_project_records(cursor, value):
    query = f"SELECT id FROM project WHERE label = '{value}'"
    cursor.execute(query)
    return cursor.fetchall()