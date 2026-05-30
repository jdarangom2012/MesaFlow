from django.conf import settings
from django.db import models
from django.db.models import Q

from orders.models import Order
from restaurants.models import Restaurant


class CashRegisterSession(models.Model):
    STATUS_OPEN = 'OPEN'
    STATUS_CLOSED = 'CLOSED'

    STATUS_CHOICES = [
        (STATUS_OPEN, 'Abierta'),
        (STATUS_CLOSED, 'Cerrada'),
    ]

    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='cash_sessions')
    opened_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='opened_cash_sessions')
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='closed_cash_sessions',
        null=True,
        blank=True,
    )
    opening_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    expected_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    actual_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    difference = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_tips = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN)
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['restaurant'],
                condition=Q(status='OPEN'),
                name='unique_open_cash_session_per_restaurant',
            ),
        ]
        ordering = ['-opened_at']

    def __str__(self):
        return f'Caja {self.restaurant.name} - {self.get_status_display()}'


class CashMovement(models.Model):
    TYPE_INCOME = 'INCOME'
    TYPE_EXPENSE = 'EXPENSE'
    TYPE_ORDER_PAYMENT = 'ORDER_PAYMENT'

    TYPE_CHOICES = [
        (TYPE_INCOME, 'Ingreso'),
        (TYPE_EXPENSE, 'Gasto'),
        (TYPE_ORDER_PAYMENT, 'Pago orden'),
    ]

    PAYMENT_METHOD_CHOICES = Order.PAYMENT_METHOD_CHOICES

    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='cash_movements')
    session = models.ForeignKey(CashRegisterSession, on_delete=models.CASCADE, related_name='movements')
    order = models.OneToOneField(Order, on_delete=models.SET_NULL, related_name='cash_movement', null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='cash_movements')
    movement_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='CASH')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_movement_type_display()} ${self.amount} - {self.session.restaurant.name}'
