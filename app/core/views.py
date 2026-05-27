from django.shortcuts import render
from products.models import ProductCategory, Product
from tables.models import RestaurantTable

def home(request):
    return render(request, 'home.html')


def dashboard(request):
    return render(request, 'dashboard/index.html')


from django.http import HttpResponse

def pos(request):

    categories = ProductCategory.objects.filter(is_active=True)

    products = Product.objects.filter(is_available=True)

    tables = RestaurantTable.objects.all()

    context = {
        'categories': categories,
        'products': products,
        'tables': tables,
    }

    return render(request, 'pos/index.html', context)