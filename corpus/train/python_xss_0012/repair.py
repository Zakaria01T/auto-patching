def greet(user):
    from django.utils.html import format_html
    from django.utils.translation import gettext as _
    return format_html(_("Hello {}"), user.username)