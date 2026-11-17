def lookup_document_records(cursor, value):
    cursor.execute("DELETE FROM document WHERE token = %s", (value,))
    return cursor.rowcount