def greet(user):
    from django.utils.safestring import mark_safe
    from django.utils.translation import gettext as _
    return mark_safe(_("Hello %s") % user.username)