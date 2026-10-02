from django.shortcuts import render, get_object_or_404
from .models import Product
from category.models import Category
from carts.views import _cart_id
from carts.models import CartItem
from django.core.paginator import Paginator
from django.db.models import Q
from recommendations.recommender import get_recommendations


def store(request, category_slug=None):
    categories = None
    products = None

    # Filter products by category if a category is selected
    if category_slug != None:
        categories = get_object_or_404(Category, slug=category_slug)
        products = Product.objects.filter(
            category=categories,
            is_available=True
        )

        # Paginate category products
        paginator = Paginator(products, 6)
        page = request.GET.get('page')
        paged_products = paginator.get_page(page)
        product_count = products.count()

    else:
        # Display all available products
        products = Product.objects.all().filter(is_available=True)

        # Paginate all products
        paginator = Paginator(products, 6)
        page = request.GET.get('page')
        paged_products = paginator.get_page(page)
        product_count = products.count()

    context = {
        'products': paged_products,
        'product_count': products.count(),
    }

    return render(request, 'store/store.html', context)


def product_detail(request, category_slug, product_slug):
    try:
        # Get the selected product
        single_product = Product.objects.get(
            category__slug=category_slug,
            slug=product_slug
        )

        # Check whether the product is already in the cart
        in_cart = CartItem.objects.filter(
            cart__cart_id=_cart_id(request),
            product=single_product
        ).exists()

    except Exception as e:
        raise e

    # Get similar product recommendations
    recommendations = get_recommendations(
        single_product.id,
        num_recommendations=4
    )

    context = {
        'single_product': single_product,
        'in_cart': in_cart,
        'recommendations': recommendations,
    }

    return render(request, 'store/product_detail.html', context)


def search(request):
    # Search products by name or description
    if 'keyword' in request.GET:
        keyword = request.GET['keyword']

        if keyword:
            products = Product.objects.order_by('-created_date').filter(
                Q(description__icontains=keyword) |
                Q(product_name__icontains=keyword)
            )
            product_count = products.count()

    context = {
        'products': products,
        'product_count': product_count,
    }

    return render(request, 'store/store.html', context)