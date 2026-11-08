def rename_team(conn, team_id, name):
    conn.execute("UPDATE teams SET name = ? WHERE id = ?", (name, team_id))
