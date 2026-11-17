def lookup_team_records(cursor, value):
    cursor.execute("SELECT id FROM team WHERE slug = %s", (value,))
    return cursor.fetchall()