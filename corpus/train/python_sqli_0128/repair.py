def lookup_profile_records(cursor, value):
    cursor.execute("SELECT id FROM profile WHERE owner = %s", (value,))
    return cursor.fetchall()