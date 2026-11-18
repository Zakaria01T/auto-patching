def example(value):
    from markupsafe import Markup, escape
    from django.utils.html import format_html
    from django.utils.safestring import mark_safe
    import html
    return render_template("profile.html", bio=Markup(user_bio))
