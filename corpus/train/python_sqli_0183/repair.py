def lookup_settings_records(cursor, value):
    cursor.execute("SELECT id FROM settings WHERE slug = %s", (value,))
    return cursor.fetchall()