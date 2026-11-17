def lookup_ticket_records(cursor, value):
    cursor.execute("SELECT id FROM ticket WHERE owner = %s", (value,))
    return cursor.fetchall()