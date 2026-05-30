from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.permissions import ADMIN, CAJERO, SUPERADMIN, role_required, tenant_filter, user_has_role

from .forms import ProductCategoryForm, ProductForm
from .models import Product, ProductCategory


@login_required
@role_required(SUPERADMIN, ADMIN)
def categories_dashboard(request):
    if not getattr(request, 'restaurant', None):
        return render(request, 'auth/403.html', {
            'message': 'Selecciona o asigna un restaurante para administrar categorías.',
        }, status=403)

    categories = list(
        ProductCategory.objects
        .filter(**tenant_filter(request))
        .annotate(products_count=Count('products'))
        .order_by('sort_order', 'name')
    )
    for category in categories:
        category.edit_form = ProductCategoryForm(instance=category)

    context = {
        'categories': categories,
        'create_form': ProductCategoryForm(),
    }

    return render(request, 'products/categories.html', context)


@login_required
@role_required(SUPERADMIN, ADMIN, CAJERO)
def products_dashboard(request):
    if not getattr(request, 'restaurant', None):
        return render(request, 'auth/403.html', {
            'message': 'Selecciona o asigna un restaurante para administrar productos.',
        }, status=403)

    products = list(
        Product.objects
        .filter(**tenant_filter(request))
        .select_related('category')
        .order_by('category__sort_order', 'category__name', 'sort_order', 'name')
    )
    can_manage_products = user_has_role(request.user, {SUPERADMIN, ADMIN})

    for product in products:
        product.edit_form = ProductForm(instance=product, restaurant=request.restaurant)

    context = {
        'products': products,
        'categories': ProductCategory.objects.filter(**tenant_filter(request)).order_by('sort_order', 'name'),
        'create_form': ProductForm(restaurant=request.restaurant),
        'can_manage_products': can_manage_products,
    }

    return render(request, 'products/index.html', context)


@login_required
@require_POST
@role_required(SUPERADMIN, ADMIN)
def category_create(request):
    if not getattr(request, 'restaurant', None):
        messages.error(request, 'No hay restaurante activo para crear categorías.')
        return redirect('products:categories')

    form = ProductCategoryForm(request.POST)

    if form.is_valid():
        category = form.save(commit=False)
        category.restaurant = request.restaurant
        category.save()
        messages.success(request, f'Categoría {category.name} creada correctamente.')
    else:
        messages.error(request, 'Revisa los campos del formulario.')

    return redirect('products:categories')


@login_required
@require_POST
@role_required(SUPERADMIN, ADMIN)
def category_update(request, category_id):
    category = get_object_or_404(ProductCategory, id=category_id, **tenant_filter(request))
    form = ProductCategoryForm(request.POST, instance=category)

    if form.is_valid():
        form.save()
        messages.success(request, f'Categoría {category.name} actualizada.')
    else:
        messages.error(request, 'No se pudo actualizar la categoría. Revisa los campos.')

    return redirect('products:categories')


@login_required
@require_POST
@role_required(SUPERADMIN, ADMIN)
def category_toggle(request, category_id):
    category = get_object_or_404(ProductCategory, id=category_id, **tenant_filter(request))
    category.is_active = not category.is_active
    category.save(update_fields=['is_active'])
    state = 'activada' if category.is_active else 'desactivada'
    messages.success(request, f'Categoría {category.name} {state}.')

    return redirect('products:categories')


@login_required
@require_POST
@role_required(SUPERADMIN, ADMIN)
def product_create(request):
    if not getattr(request, 'restaurant', None):
        messages.error(request, 'No hay restaurante activo para crear productos.')
        return redirect('products_dashboard')

    form = ProductForm(request.POST, request.FILES, restaurant=request.restaurant)

    if form.is_valid():
        product = form.save(commit=False)
        product.restaurant = request.restaurant
        product.is_available = product.is_active
        product.save()
        messages.success(request, f'Producto {product.name} creado correctamente.')
    else:
        messages.error(request, 'Revisa los campos del producto.')

    return redirect('products_dashboard')


@login_required
@require_POST
@role_required(SUPERADMIN, ADMIN)
def product_update(request, product_id):
    product = get_object_or_404(Product, id=product_id, **tenant_filter(request))
    form = ProductForm(request.POST, request.FILES, instance=product, restaurant=request.restaurant)

    if form.is_valid():
        product = form.save(commit=False)
        product.is_available = product.is_active
        product.save()
        messages.success(request, f'Producto {product.name} actualizado.')
    else:
        messages.error(request, 'No se pudo actualizar el producto. Revisa los campos.')

    return redirect('products_dashboard')


@login_required
@require_POST
@role_required(SUPERADMIN, ADMIN)
def product_toggle(request, product_id):
    product = get_object_or_404(Product, id=product_id, **tenant_filter(request))
    product.is_active = not product.is_active
    product.is_available = product.is_active
    product.save(update_fields=['is_active', 'is_available'])
    state = 'activado' if product.is_active else 'desactivado'
    messages.success(request, f'Producto {product.name} {state}.')

    return redirect('products_dashboard')
