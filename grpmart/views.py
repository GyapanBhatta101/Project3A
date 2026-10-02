from django.shortcuts import render
from store.models import Product
def home(request):
    # Get all available products ordered by creation date
    products = Product.objects.all().filter(is_available=True).order_by('created_date')
    context = {
        'products': products,
    }

    return render(request,'home.html',context)
