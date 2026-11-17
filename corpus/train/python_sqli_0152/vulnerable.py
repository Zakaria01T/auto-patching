def lookup_account_records(cursor, value):
    query = f"SELECT id FROM account WHERE label = '{value}'"
    cursor.execute(query)
    return cursor.fetchall()