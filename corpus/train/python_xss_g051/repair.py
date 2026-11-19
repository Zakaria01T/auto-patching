def review_summary(request):
    from django.utils.html import format_html
    reviewer = request.GET.get("reviewer", "")
    return format_html("<div class='review'>{}</div>", reviewer)
