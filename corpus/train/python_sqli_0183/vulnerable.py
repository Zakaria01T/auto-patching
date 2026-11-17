def lookup_settings_records(cursor, value):
    query = "SELECT id FROM settings WHERE slug = '{}'".format(value)
    cursor.execute(query)
    return cursor.fetchall()