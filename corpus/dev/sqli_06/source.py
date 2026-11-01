def get_product(conn, name):
    query = "SELECT * FROM products WHERE name = '{}'".format(name)
    return conn.execute(query).fetchall()
