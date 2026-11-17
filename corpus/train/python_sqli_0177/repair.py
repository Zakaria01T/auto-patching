def lookup_catalog_records(cursor, value):
    cursor.execute("SELECT id FROM catalog WHERE label = %s", (value,))
    return cursor.fetchall()