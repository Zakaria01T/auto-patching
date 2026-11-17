def lookup_project_records(cursor, value):
    cursor.execute("SELECT id FROM project WHERE label = %s", (value,))
    return cursor.fetchall()