def lookup_profile_records(cursor, value):
    cursor.execute("SELECT id FROM profile WHERE owner = '" + value + "'")
    return cursor.fetchall()