from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from products.models import ProductCategory, Product
from tables.models import RestaurantTable

def home(request):
    return render(request, 'home.html')


@login_required
def dashboard(request):
    return render(request, 'dashboard/index.html')


from django.http import HttpResponse

@login_required
def pos(request):

    categories = ProductCategory.objects.filter(is_active=True, restaurant=request.restaurant)

    products = Product.objects.filter(is_available=True, restaurant=request.restaurant)

    tables = RestaurantTable.objects.filter(restaurant=request.restaurant)

    context = {
        'categories': categories,
        'products': products,
        'tables': tables,
    }

    return render(request, 'pos/index.html', context)


def qr_menu(request, table_id):
    table = get_object_or_404(RestaurantTable, id=table_id)
    categories = (
        ProductCategory.objects
        .filter(is_active=True, restaurant=table.restaurant)
        .prefetch_related('products')
        .order_by('name')
    )
    products = (
        Product.objects
        .filter(is_available=True, restaurant=table.restaurant)
        .select_related('category')
        .order_by('category__name', 'name')
    )

    context = {
        'table': table,
        'categories': categories,
        'products': products,
    }

    return render(request, 'menu/index.html', context)
