def lookup_audit_records(cursor, value):
    query = "UPDATE audit SET active = 0 WHERE email = '" + value + "'"
    cursor.execute(query)
    return cursor.rowcount