def playlist_item(track, artist):
    title = track.strip()
    performer = artist.strip()
    return f"<li class='track'>{title} - {performer}</li>"
