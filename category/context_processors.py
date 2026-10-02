from .models import Category

def menu_links(request):
    # Get all categories for the navigation menu
    links = Category.objects.all()
    return dict(links=links)