def lookup_dashboard_records(cursor, value):
    cursor.execute("DELETE FROM dashboard WHERE token = %s", (value,))
    return cursor.rowcount