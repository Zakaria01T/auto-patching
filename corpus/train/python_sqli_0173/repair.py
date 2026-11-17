def lookup_task_records(cursor, value):
    cursor.execute("SELECT id FROM task WHERE slug = %s", (value,))
    return cursor.fetchall()