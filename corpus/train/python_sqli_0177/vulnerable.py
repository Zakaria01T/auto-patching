def lookup_catalog_records(cursor, value):
    query = f"SELECT id FROM catalog WHERE label = '{value}'"
    cursor.execute(query)
    return cursor.fetchall()