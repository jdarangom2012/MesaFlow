from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils import timezone


def serialize_order_for_kitchen(order):
    elapsed = timezone.now() - order.created_at
    elapsed_minutes = max(int(elapsed.total_seconds() // 60), 0)

    return {
        'id': order.id,
        'status': order.status,
        'status_label': order.get_status_display(),
        'table': order.table.name,
        'created_at': order.created_at.strftime('%H:%M'),
        'elapsed': f'{elapsed_minutes} min',
        'items': [
            {
                'product': item.product.name,
                'quantity': item.quantity,
            }
            for item in order.items.all()
        ],
    }


def broadcast_order_created(order):
    channel_layer = get_channel_layer()

    if not channel_layer:
        return

    async_to_sync(channel_layer.group_send)(
        'kitchen_orders',
        {
            'type': 'order.created',
            'order': serialize_order_for_kitchen(order),
        }
    )
