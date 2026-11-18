def donation_receipt(request):
    from django.utils.html import format_html
    donor = request.GET.get("donor", "")
    return format_html("<p class='receipt'>Thank you, {}.</p>", donor)
