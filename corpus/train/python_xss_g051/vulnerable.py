def review_summary(request):
    reviewer = request.GET.get("reviewer", "")
    return (
        f"<div class='review'>{reviewer}</div>"
    )
