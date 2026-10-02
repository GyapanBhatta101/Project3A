
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from carts.models import CartItem
from store.models import Product
from .forms import OrderForm
import datetime
from .models import Order, Payment, OrderProduct
from django.contrib.auth.decorators import login_required

# PAYMENTS PAGE
@login_required(login_url='login')
def payments(request):
    return render(request, 'orders/payments.html')

# PLACE ORDER
@login_required(login_url='login')
def place_order(request):

    current_user = request.user

    # Get cart items
    cart_items = CartItem.objects.filter(
        user=current_user,
        is_active=True
    )

    # If cart is empty
    cart_count = cart_items.count()

    if cart_count <= 0:
        return redirect('store')

    # Calculate total
    total = 0
    quantity = 0

    for cart_item in cart_items:
        total += cart_item.product.price * cart_item.quantity
        quantity += cart_item.quantity

    # Calculate tax
    tax = (2 * total) / 100

    # Grand total
    grand_total = total + tax

    if request.method == 'POST':

        form = OrderForm(request.POST)

        if form.is_valid():

            # Create Order
            data = Order()

            data.user = current_user
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.phone = form.cleaned_data['phone']
            data.email = form.cleaned_data['email']
            data.address_line_1 = form.cleaned_data['address_line_1']
            data.address_line_2 = form.cleaned_data['address_line_2']
            data.country = form.cleaned_data['country']
            data.state = form.cleaned_data['state']
            data.city = form.cleaned_data['city']
            data.order_note = form.cleaned_data['order_note']

            data.order_total = grand_total
            data.tax = tax

            data.ip = request.META.get('REMOTE_ADDR')

            data.save()

            # Generate order number
            yr = int(datetime.date.today().strftime('%Y'))
            mt = int(datetime.date.today().strftime('%m'))
            dt = int(datetime.date.today().strftime('%d'))

            current_date = datetime.date(yr, mt, dt).strftime('%Y%m%d')

            order_number = current_date + str(data.id)

            data.order_number = order_number

            data.save()

            # Get the newly created order
            order = Order.objects.get(
                user=current_user,
                is_ordered=False,
                order_number=order_number
            )

            context = {
                'order': order,
                'cart_items': cart_items,
                'total': total,
                'tax': tax,
                'grand_total': grand_total,
            }
            # Display payment page with order details
            return render(
                request,
                'orders/payments.html',
                context
            )

    else:
        return redirect('checkout')

    return redirect('checkout')

# PAYMENT SUCCESS
@login_required(login_url='login')
def payment_success(request):
    if request.method == 'POST':
        order_number = request.POST.get('order_number')

        try:
            order = Order.objects.get(
                order_number=order_number,
                user=request.user,
                is_ordered=False
            )

            # Create payment
            payment = Payment.objects.create(
                user=request.user,
                payment_id='DEMO-' + order.order_number,
                payment_method='Demo Payment',
                amount_paid=str(order.order_total),
                status='Completed',
            )

            # Update order
            order.payment = payment
            order.is_ordered = True
            order.status = 'Completed'
            order.save()

            # Get active cart items
            cart_items = CartItem.objects.filter(
                user=request.user,
                is_active=True
            )

            # Create OrderProduct records
            for item in cart_items:
                orderproduct = OrderProduct.objects.create(
                    order=order,
                    payment=payment,
                    user=request.user,
                    product=item.product,
                    quantity=item.quantity,
                    product_price=item.product.price,
                    ordered=True
                )

                # Copy variations
                product_variation = item.variations.all()
                orderproduct.variations.set(product_variation)

                # Reduce stock
                product = Product.objects.get(id=item.product_id)
                product.stock -= item.quantity
                product.save()

            # Deactivate cart items
            cart_items.update(is_active=False)

            # REDIRECT TO ORDER COMPLETE PAGE
            return redirect('order_complete', order_number=order.order_number)

        except Order.DoesNotExist:
            return redirect('store')

    return redirect('checkout')
@login_required(login_url='login')
def order_complete(request, order_number):
    try:
        # Get the completed order
        order = Order.objects.get(
            order_number=order_number,
            user=request.user,
            is_ordered=True
        )
        # Get products belonging to the order
        order_products = OrderProduct.objects.filter(
            order=order
        )

        context = {
            'order': order,
            'order_products': order_products,
        }

        return render(
            request,
            'orders/order_complete.html',
            context
        )

    except Order.DoesNotExist:
        return redirect('store')

