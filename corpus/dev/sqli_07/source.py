def search_books(conn, term):
    query = f"SELECT title FROM books WHERE title LIKE '%{term}%'"
    return conn.execute(query).fetchall()
