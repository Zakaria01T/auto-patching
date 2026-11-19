def reset_notice(request):
    from django.utils.html import format_html
    email_hint = request.GET.get("email_hint", "")
    return format_html("<p class='reset'>Check {} for the reset link.</p>", email_hint)
