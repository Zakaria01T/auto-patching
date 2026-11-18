def playlist_item(track, artist):
    import html
    title = track.strip()
    performer = artist.strip()
    safe_title = html.escape(title, quote=True)
    safe_performer = html.escape(performer, quote=True)
    return "<li class='track'>{0} - {1}</li>".format(safe_title, safe_performer)
