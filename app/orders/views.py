import json
from decimal import Decimal

from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from products.models import Product
from tables.models import RestaurantTable

from .models import Order, OrderItem


@require_POST
def create_order(request):
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON inválido'}, status=400)

    table_id = payload.get('table_id')
    items = payload.get('items', [])

    if not table_id:
        return JsonResponse({'success': False, 'error': 'Mesa requerida'}, status=400)

    if not isinstance(items, list) or not items:
        return JsonResponse({'success': False, 'error': 'Productos requeridos'}, status=400)

    try:
        table = RestaurantTable.objects.get(id=table_id)
    except RestaurantTable.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Mesa no encontrada'}, status=404)

    product_quantities = {}

    for item in items:
        product_id = item.get('product_id')
        quantity = item.get('quantity')

        if not product_id:
            return JsonResponse({'success': False, 'error': 'Producto requerido'}, status=400)

        try:
            product_id = int(product_id)
        except (TypeError, ValueError):
            return JsonResponse({'success': False, 'error': 'Producto inválido'}, status=400)

        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            return JsonResponse({'success': False, 'error': 'Cantidad inválida'}, status=400)

        if quantity <= 0:
            return JsonResponse({'success': False, 'error': 'La cantidad debe ser mayor a 0'}, status=400)

        product_quantities[product_id] = product_quantities.get(product_id, 0) + quantity

    products = Product.objects.filter(id__in=product_quantities.keys())
    products_by_id = {product.id: product for product in products}

    if len(products_by_id) != len(product_quantities):
        return JsonResponse({'success': False, 'error': 'Uno o más productos no existen'}, status=404)

    subtotal = Decimal('0.00')
    order_items = []

    for product_id, quantity in product_quantities.items():
        product = products_by_id[product_id]
        item_subtotal = product.price * quantity
        subtotal += item_subtotal
        order_items.append({
            'product': product,
            'quantity': quantity,
            'unit_price': product.price,
            'subtotal': item_subtotal,
        })

    tax = (subtotal * Decimal('0.19')).quantize(Decimal('0.01'))
    total = subtotal + tax

    with transaction.atomic():
        order = Order.objects.create(
            table=table,
            status='OPEN',
            subtotal=subtotal,
            tax=tax,
            total=total,
        )

        OrderItem.objects.bulk_create([
            OrderItem(
                order=order,
                product=item['product'],
                quantity=item['quantity'],
                unit_price=item['unit_price'],
                subtotal=item['subtotal'],
            )
            for item in order_items
        ])

    return JsonResponse({
        'success': True,
        'order_id': order.id,
        'total': float(total),
    })
