def bid_row(request):
    from django.utils.html import format_html
    bidder = request.GET.get("bidder", "")
    return format_html("<tr><td>{}</td></tr>", bidder)
