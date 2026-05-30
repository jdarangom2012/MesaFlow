import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer


class KitchenConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = await self.get_group_name()

        if not self.group_name:
            await self.close(code=4403)
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if getattr(self, 'group_name', None):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    @database_sync_to_async
    def get_group_name(self):
        user = self.scope.get('user')

        if not user or not user.is_authenticated:
            return None

        if user.is_superuser:
            return 'kitchen_orders_all'

        profile = getattr(user, 'restaurant_profile', None)
        if not profile or not profile.restaurant_id:
            return None

        return f'kitchen_orders_{profile.restaurant_id}'

    async def order_created(self, event):
        await self.send(text_data=json.dumps({
            'type': 'order.created',
            'order': event['order'],
        }))

    async def order_paid(self, event):
        await self.send(text_data=json.dumps({
            'type': 'order.paid',
            'order_id': event['order_id'],
        }))

    async def order_removed(self, event):
        await self.send(text_data=json.dumps({
            'type': 'order.removed',
            'order_id': event['order_id'],
        }))

    async def order_updated(self, event):
        await self.send(text_data=json.dumps({
            'type': 'order.updated',
            'order': event['order'],
        }))
