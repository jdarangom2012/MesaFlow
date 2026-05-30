from decimal import Decimal

from django.db.models import DecimalField, Q, Sum, Value
from django.db.models.functions import Coalesce

from .models import CashMovement, CashRegisterSession


ZERO_MONEY = Value(0, output_field=DecimalField(max_digits=12, decimal_places=2))


def get_open_session(restaurant):
    if not restaurant:
        return None

    return CashRegisterSession.objects.filter(
        restaurant=restaurant,
        status=CashRegisterSession.STATUS_OPEN,
    ).order_by('-opened_at').first()


def get_session_totals(session):
    if not session:
        return {
            'cash_total': Decimal('0'),
            'card_total': Decimal('0'),
            'digital_total': Decimal('0'),
            'expected_total': Decimal('0'),
            'income_total': Decimal('0'),
            'expense_total': Decimal('0'),
            'sales_total': Decimal('0'),
            'tax_total': Decimal('0'),
            'tips_total': Decimal('0'),
        }

    movements = session.movements.all()
    totals = movements.aggregate(
        cash_income=Coalesce(Sum('amount', filter=Q(payment_method='CASH', movement_type__in=['INCOME', 'ORDER_PAYMENT'])), ZERO_MONEY),
        cash_expense=Coalesce(Sum('amount', filter=Q(payment_method='CASH', movement_type='EXPENSE')), ZERO_MONEY),
        card_total=Coalesce(Sum('amount', filter=Q(payment_method='CARD', movement_type__in=['INCOME', 'ORDER_PAYMENT'])), ZERO_MONEY),
        digital_total=Coalesce(Sum('amount', filter=Q(payment_method='DIGITAL', movement_type__in=['INCOME', 'ORDER_PAYMENT'])), ZERO_MONEY),
        income_total=Coalesce(Sum('amount', filter=Q(movement_type='INCOME')), ZERO_MONEY),
        expense_total=Coalesce(Sum('amount', filter=Q(movement_type='EXPENSE')), ZERO_MONEY),
        sales_total=Coalesce(Sum('amount', filter=Q(movement_type='ORDER_PAYMENT')), ZERO_MONEY),
        tax_total=Coalesce(Sum('order__tax', filter=Q(movement_type='ORDER_PAYMENT')), ZERO_MONEY),
    )
    cash_total = session.opening_amount + totals['cash_income'] - totals['cash_expense']

    return {
        'cash_total': cash_total,
        'card_total': totals['card_total'],
        'digital_total': totals['digital_total'],
        'expected_total': cash_total,
        'income_total': totals['income_total'],
        'expense_total': totals['expense_total'],
        'sales_total': totals['sales_total'],
        'tax_total': totals['tax_total'],
        'tips_total': Decimal('0'),
    }


def record_order_payment(order, user):
    session = get_open_session(order.restaurant)

    if not session:
        return None

    movement, _created = CashMovement.objects.get_or_create(
        order=order,
        defaults={
            'restaurant': order.restaurant,
            'session': session,
            'user': user,
            'movement_type': CashMovement.TYPE_ORDER_PAYMENT,
            'payment_method': order.payment_method or 'CASH',
            'amount': order.total,
            'note': f'Pago orden #{order.id}',
        },
    )

    return movement
