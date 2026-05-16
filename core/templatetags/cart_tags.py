from django import template
from django.db.models import Sum
from core.models import Cart  # change to your app name

register = template.Library()


@register.simple_tag(takes_context=True)
def get_cart_count(context):
    request = context.get('request')

    # If request is missing
    if not request:
        return 0

    # If user not logged in
    if not request.user.is_authenticated:
        return 0

    total = Cart.objects.filter(user=request.user).aggregate(
        Sum('quantity')
    )['quantity__sum'] or 0

    return total
