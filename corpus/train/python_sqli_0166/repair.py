def lookup_product_records(cursor, value):
    cursor.execute("SELECT id FROM product WHERE owner = %s", (value,))
    return cursor.fetchall()