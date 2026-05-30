from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils import timezone


def _broadcast_to_restaurant(order, event):
    channel_layer = get_channel_layer()

    if not channel_layer:
        return

    group_names = [f'kitchen_orders_{order.restaurant_id}', 'kitchen_orders_all']
    for group_name in group_names:
        async_to_sync(channel_layer.group_send)(group_name, event)


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
    _broadcast_to_restaurant(
        order,
        {
            'type': 'order.created',
            'order': serialize_order_for_kitchen(order),
        }
    )


def broadcast_order_paid(order):
    _broadcast_to_restaurant(
        order,
        {
            'type': 'order.paid',
            'order_id': order.id,
        }
    )


def broadcast_order_removed(order):
    _broadcast_to_restaurant(
        order,
        {
            'type': 'order.removed',
            'order_id': order.id,
        }
    )


def broadcast_order_updated(order):
    _broadcast_to_restaurant(
        order,
        {
            'type': 'order.updated',
            'order': serialize_order_for_kitchen(order),
        }
    )
