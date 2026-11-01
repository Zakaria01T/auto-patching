def delete_session(conn, token):
    query = "DELETE FROM sessions WHERE token = '" + token + "'"
    conn.execute(query)
