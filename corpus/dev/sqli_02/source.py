def find_orders(conn, customer_id):
    query = f"SELECT * FROM orders WHERE customer_id = {customer_id}"
    return conn.execute(query).fetchall()
