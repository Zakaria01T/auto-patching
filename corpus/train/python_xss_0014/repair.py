def example(value):
    from markupsafe import Markup, escape
    from django.utils.html import format_html
    import html
    import bleach
    return render_template("profile.html", bio=user_bio)
