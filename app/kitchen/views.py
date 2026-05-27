from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from orders.models import Order


@require_http_methods(['GET', 'POST'])
@login_required
def kitchen_display(request):
    if request.method == 'POST':
        order = get_object_or_404(Order, id=request.POST.get('order_id'), restaurant=request.restaurant)
        next_status = request.POST.get('status')

        if next_status in ['PREPARING', 'READY']:
            order.status = next_status
            order.save(update_fields=['status'])

        return redirect('kitchen')

    orders = (
        Order.objects
        .filter(status__in=['OPEN', 'PREPARING'], restaurant=request.restaurant)
        .select_related('table')
        .prefetch_related('items__product')
        .order_by('created_at')
    )

    return render(request, 'kitchen/index.html', {'orders': orders})
