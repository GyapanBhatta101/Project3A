from .models import Cart, CartItem
from .views import _cart_id


def counter(request):
    # Initialize cart item count
    cart_count = 0
    # Skip cart count on admin pages
    if 'admin' in request.path:
        return {}

    try:
        # Get active cart items for logged-in users
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(
                user=request.user,
                is_active=True
            )
        else:
            # Get active cart items for guest users
            cart = Cart.objects.get(cart_id=_cart_id(request))

            cart_items = CartItem.objects.filter(
                cart=cart,
                is_active=True
            )

        # Calculate total number of items
        for cart_item in cart_items:
            cart_count += cart_item.quantity

    except Cart.DoesNotExist:
        # Return zero when no cart exists
        cart_count = 0

    return {
        'cart_count': cart_count
    }