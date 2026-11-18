def render_episode_card(episode_title):
    import html
    return "<article class='episode'>{}</article>".format(html.escape(episode_title, quote=True))
