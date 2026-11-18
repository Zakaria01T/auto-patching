def leaderboard_row(player_name):
    import html
    return (
        "<tr class='rank'><td>{}</td></tr>".format(html.escape(player_name, quote=True))
    )
