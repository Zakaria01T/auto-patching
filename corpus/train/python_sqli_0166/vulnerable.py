def lookup_product_records(cursor, value):
    cursor.execute("SELECT id FROM product WHERE owner = '" + value + "'")
    return cursor.fetchall()