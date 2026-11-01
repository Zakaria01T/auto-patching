def add_user(conn, name, email):
    query = "INSERT INTO users (name, email) VALUES ('" + name + "', '" + email + "')"
    conn.execute(query)
