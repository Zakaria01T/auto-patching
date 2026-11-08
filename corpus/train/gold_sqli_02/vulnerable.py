def rename_team(conn, team_id, name):
    conn.execute(f"UPDATE teams SET name = '{name}' WHERE id = {team_id}")
