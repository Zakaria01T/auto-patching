def bid_row(request):
    bidder = request.GET.get("bidder", "")
    return (
        "<tr><td>" + bidder + "</td></tr>"
    )
