def log_login(conn, username):
    query = f"INSERT INTO logins (username) VALUES ('{username}')"
    conn.execute(query)
