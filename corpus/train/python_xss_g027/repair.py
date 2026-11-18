def render_coupon_banner(coupon_code):
    from django.http import HttpRequest
    from django.utils.html import format_html
    code = getattr(HttpRequest, 'GET', {}).get('code', coupon_code)
    return format_html("<div class='coupon'>{}</div>", code)
