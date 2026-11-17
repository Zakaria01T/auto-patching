def lookup_account_records(cursor, value):
    cursor.execute("SELECT id FROM account WHERE label = %s", (value,))
    return cursor.fetchall()