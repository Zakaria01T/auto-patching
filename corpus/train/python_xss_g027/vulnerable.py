def render_coupon_banner(coupon_code):
    from django.http import HttpRequest
    code = getattr(HttpRequest, 'GET', {}).get('code', coupon_code)
    return f"<div class='coupon'>{code}</div>"
