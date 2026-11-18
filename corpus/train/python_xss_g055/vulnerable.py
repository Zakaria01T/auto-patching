def reset_notice(request):
    email_hint = request.GET.get("email_hint", "")
    return (
        f"<p class='reset'>Check {email_hint} for the reset link.</p>"
    )
