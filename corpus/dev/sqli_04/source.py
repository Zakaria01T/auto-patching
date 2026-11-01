def update_email(conn, user_id, email):
    query = f"UPDATE users SET email = '{email}' WHERE id = {user_id}"
    conn.execute(query)
