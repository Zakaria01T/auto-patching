def donation_receipt(request):
    donor = request.GET.get("donor", "")
    return (
        f"<p class='receipt'>Thank you, {donor}.</p>"
    )
