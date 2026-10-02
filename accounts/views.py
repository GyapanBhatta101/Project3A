from django.shortcuts import render, redirect
from .forms import RegistrationForm
from .models import Account, UserProfile
from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required
from carts.views import _cart_id
from carts.models import Cart, CartItem
from orders.models import Order, OrderProduct
import requests


def register(request):
    # Handle user registration
    if request.method == 'POST':
        form = RegistrationForm(request.POST)

        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            phone_number = form.cleaned_data['phone_number']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            # Generate username from email
            username = email.split("@")[0]

            # Create the user account
            user = Account.objects.create_user(
                first_name=first_name,
                last_name=last_name,
                email=email,
                username=username,
                password=password
            )

            user.phone_number = phone_number
            user.save()

            # Create profile for the new user
            UserProfile.objects.create(user=user)

            messages.success(request, 'Registration Successful')
            return redirect('register')

    else:
        form = RegistrationForm()

    context = {'form': form}

    return render(
        request,
        'accounts/register.html',
        context
    )


def login(request):
    # Handle user login
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        user = auth.authenticate(
            email=email,
            password=password
        )

        if user is not None:

            try:
                # Get the guest cart from the current session
                cart = Cart.objects.get(
                    cart_id=_cart_id(request)
                )

                is_cart_item_exists = CartItem.objects.filter(
                    cart=cart
                ).exists()

                if is_cart_item_exists:

                    # Get variations from guest cart items
                    cart_item = CartItem.objects.filter(cart=cart)
                    product_variation = []

                    for item in cart_item:
                        variation = item.variations.all()
                        product_variation.append(list(variation))

                    # Get existing user cart items
                    cart_item = CartItem.objects.filter(user=user)
                    ex_var_list = []
                    id = []

                    for item in cart_item:
                        existing_variation = item.variations.all()
                        ex_var_list.append(list(existing_variation))
                        id.append(item.id)

                    # Merge guest cart items with the user cart
                    for pr in product_variation:

                        if pr in ex_var_list:
                            index = ex_var_list.index(pr)
                            item_id = id[index]

                            item = CartItem.objects.get(id=item_id)
                            item.quantity += 1
                            item.user = user
                            item.save()

                        else:
                            cart_item = CartItem.objects.filter(
                                cart=cart
                            )

                            for item in cart_item:
                                item.user = user
                                item.save()

            except:
                pass

            # Log the user in
            auth.login(request, user)
            messages.success(request, 'You are logged in.')

            # Redirect the user to the previous page
            url = request.META.get('HTTP_REFERER')

            try:
                query = requests.utils.urlparse(url).query

                # Get the next page from the URL
                params = dict(
                    x.split('=') for x in query.split('&')
                )

                if 'next' in params:
                    nextPage = params['next']
                    return redirect(nextPage)

            except:
                return redirect('dashboard')

        else:
            # Show error for invalid credentials
            messages.error(
                request,
                'Invalid login credentials'
            )

            return redirect('login')

    return render(request, 'accounts/login.html')


@login_required(login_url='login')
def logout(request):
    # Log out the current user
    auth.logout(request)

    messages.success(
        request,
        'You are logged out.'
    )

    return redirect('login')


@login_required(login_url='login')
def dashboard(request):

    # Get the user's completed orders
    orders = Order.objects.order_by(
        '-created_at'
    ).filter(
        user_id=request.user.id,
        is_ordered=True
    )

    orders_count = orders.count()

    # Get or create the user's profile
    userprofile, created = UserProfile.objects.get_or_create(
        user=request.user
    )

    context = {
        'orders_count': orders_count,
        'userprofile': userprofile,
    }

    return render(
        request,
        'accounts/dashboard.html',
        context
    )


@login_required(login_url='login')
def my_orders(request):

    # Get all completed orders for the user
    orders = Order.objects.filter(
        user=request.user,
        is_ordered=True
    ).order_by('-created_at')

    context = {
        'orders': orders,
    }

    return render(
        request,
        'accounts/my_orders.html',
        context
    )


@login_required(login_url='login')
def order_detail(request, order_id):

    # Get the selected completed order
    order = Order.objects.get(
        order_number=order_id,
        user=request.user,
        is_ordered=True
    )

    # Get products included in the order
    order_products = OrderProduct.objects.filter(
        order=order
    )

    # Calculate order subtotal
    subtotal = 0

    for item in order_products:
        subtotal += item.product_price * item.quantity

    context = {
        'order_products': order_products,
        'order': order,
        'subtotal': subtotal,
    }

    return render(
        request,
        'accounts/order_detail.html',
        context
    )