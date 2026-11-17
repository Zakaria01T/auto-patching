def lookup_audit_records(cursor, value):
    cursor.execute("UPDATE audit SET active = 0 WHERE email = %s", (value,))
    return cursor.rowcount