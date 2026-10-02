from django.shortcuts import render, redirect, get_object_or_404
from store.models import Product, Variation
from .models import Cart, CartItem
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required


def _cart_id(request):
    # Get or create a session ID for the guest cart
    cart = request.session.session_key

    if not cart:
        cart = request.session.create()

    return cart


def add_cart(request, product_id):
    # Get the selected product
    current_user = request.user
    product = Product.objects.get(id=product_id)

    # Handle cart for authenticated users
    if current_user.is_authenticated:
        product_variation = []

        # Get selected product variations
        if request.method == 'POST':
            for item in request.POST:
                key = item
                value = request.POST[key]

                try:
                    variation = Variation.objects.get(
                        product=product,
                        variation_category__iexact=key,
                        variation_value__iexact=value
                    )
                    product_variation.append(variation)
                except:
                    pass

        # Check if product already exists in the user's cart
        is_cart_item_exists = CartItem.objects.filter(
            product=product,
            user=current_user
        ).exists()

        if is_cart_item_exists:
            cart_item = CartItem.objects.filter(
                product=product,
                user=current_user
            )

            # Store existing variations and item IDs
            ex_var_list = []
            id = []

            for item in cart_item:
                existing_variation = item.variations.all()
                ex_var_list.append(list(existing_variation))
                id.append(item.id)

            if product_variation in ex_var_list:
                # Increase quantity of existing item
                index = ex_var_list.index(product_variation)
                item_id = id[index]

                item = CartItem.objects.get(
                    product=product,
                    id=item_id
                )

                item.quantity += 1
                item.save()

            else:
                # Create a new cart item with selected variations
                item = CartItem.objects.create(
                    product=product,
                    quantity=1,
                    user=current_user
                )

                if len(product_variation) > 0:
                    item.variations.clear()
                    item.variations.add(*product_variation)

                item.save()

        else:
            # Add product as a new cart item
            cart_item = CartItem.objects.create(
                product=product,
                quantity=1,
                user=current_user,
            )

            if len(product_variation) > 0:
                cart_item.variations.clear()
                cart_item.variations.add(*product_variation)

            cart_item.save()

        return redirect('cart')

    # Handle cart for guest users
    else:
        product_variation = []

        # Get selected product variations
        if request.method == 'POST':
            for item in request.POST:
                key = item
                value = request.POST[key]

                try:
                    variation = Variation.objects.get(
                        product=product,
                        variation_category__iexact=key,
                        variation_value__iexact=value
                    )
                    product_variation.append(variation)
                except:
                    pass

        # Get or create the guest cart
        try:
            cart = Cart.objects.get(
                cart_id=_cart_id(request)
            )
        except Cart.DoesNotExist:
            cart = Cart.objects.create(
                cart_id=_cart_id(request)
            )

        cart.save()

        # Check if product already exists in the guest cart
        is_cart_item_exists = CartItem.objects.filter(
            product=product,
            cart=cart
        ).exists()

        if is_cart_item_exists:
            cart_item = CartItem.objects.filter(
                product=product,
                cart=cart
            )

            # Store existing variations and item IDs
            ex_var_list = []
            id = []

            for item in cart_item:
                existing_variation = item.variations.all()
                ex_var_list.append(list(existing_variation))
                id.append(item.id)

            if product_variation in ex_var_list:
                # Increase quantity of existing item
                index = ex_var_list.index(product_variation)
                item_id = id[index]

                item = CartItem.objects.get(
                    product=product,
                    id=item_id
                )

                item.quantity += 1
                item.save()

            else:
                # Create a new cart item with variations
                item = CartItem.objects.create(
                    product=product,
                    quantity=1,
                    cart=cart
                )

                if len(product_variation) > 0:
                    item.variations.clear()
                    item.variations.add(*product_variation)

                item.save()

        else:
            # Add product as a new guest cart item
            cart_item = CartItem.objects.create(
                product=product,
                quantity=1,
                cart=cart,
            )

            if len(product_variation) > 0:
                cart_item.variations.clear()
                cart_item.variations.add(*product_variation)

            cart_item.save()

        return redirect('cart')


def remove_cart(request, product_id, cart_item_id):

    # Get the selected product
    product = get_object_or_404(Product, id=product_id)

    try:
        # Get cart item based on user type
        if request.user.is_authenticated:
            cart_item = CartItem.objects.get(
                product=product,
                user=request.user,
                id=cart_item_id
            )
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))

            cart_item = CartItem.objects.get(
                product=product,
                cart=cart,
                id=cart_item_id
            )

        # Reduce quantity or remove the item
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()

    except:
        pass

    return redirect('cart')


def remove_cart_item(request, product_id, cart_item_id):

    # Get the selected product
    product = get_object_or_404(Product, id=product_id)

    # Find the cart item based on user type
    if request.user.is_authenticated:
        cart_item = CartItem.objects.get(
            product=product,
            user=request.user,
            id=cart_item_id
        )
    else:
        cart = Cart.objects.get(cart_id=_cart_id(request))

        cart_item = CartItem.objects.get(
            product=product,
            cart=cart,
            id=cart_item_id
        )

    # Remove the item completely
    cart_item.delete()

    return redirect('cart')


def cart(request, total=0, quantity=0, cart_items=None):

    try:
        tax = 0
        grand_total = 0

        # Get active cart items for the current user
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(
                user=request.user,
                is_active=True
            )
        else:
            # Get active cart items for guest users
            cart = Cart.objects.get(
                cart_id=_cart_id(request)
            )

            cart_items = CartItem.objects.filter(
                cart=cart,
                is_active=True
            )

        # Calculate total and quantity
        for cart_item in cart_items:
            total += (
                cart_item.product.price *
                cart_item.quantity
            )
            quantity += cart_item.quantity

        # Calculate tax and grand total
        tax = (2 * total) / 100
        grand_total = total + tax

    except ObjectDoesNotExist:
        pass

    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': grand_total,
    }

    return render(
        request,
        'store/cart.html',
        context
    )


@login_required(login_url='login')
def checkout(request, total=0, quantity=0, cart_items=None):

    try:
        tax = 0
        grand_total = 0

        # Get active cart items
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(
                user=request.user,
                is_active=True
            )
        else:
            cart = Cart.objects.get(
                cart_id=_cart_id(request)
            )

            cart_items = CartItem.objects.filter(
                cart=cart,
                is_active=True
            )

        # Calculate total and quantity
        for cart_item in cart_items:
            total += (
                cart_item.product.price *
                cart_item.quantity
            )
            quantity += cart_item.quantity

        # Calculate tax and grand total
        tax = (2 * total) / 100
        grand_total = total + tax

    except ObjectDoesNotExist:
        pass

    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': grand_total,
    }

    return render(
        request,
        'store/checkout.html',
        context
    )