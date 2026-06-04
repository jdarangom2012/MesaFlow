from decimal import Decimal

from django.db.models import DecimalField, Q, Sum, Value
from django.db.models.functions import Coalesce

from .models import CashMovement, CashRegisterSession


ZERO_MONEY = Value(0, output_field=DecimalField(max_digits=12, decimal_places=2))
SALE_TYPES = [CashMovement.TYPE_SALE, CashMovement.TYPE_ORDER_PAYMENT]


class CashRegisterClosedError(Exception):
    pass


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
            'qr_total': Decimal('0'),
            'expected_total': Decimal('0'),
            'expected_cash': Decimal('0'),
            'income_total': Decimal('0'),
            'income_cash': Decimal('0'),
            'expense_total': Decimal('0'),
            'expense_cash': Decimal('0'),
            'sales_total': Decimal('0'),
            'tax_total': Decimal('0'),
            'tips_total': Decimal('0'),
            'opening_amount': Decimal('0'),
        }

    movements = session.movements.all()
    totals = movements.aggregate(
        cash_sales=Coalesce(Sum('amount', filter=Q(payment_method=CashMovement.PAYMENT_CASH, movement_type__in=SALE_TYPES)), ZERO_MONEY),
        cash_income=Coalesce(Sum('amount', filter=Q(payment_method=CashMovement.PAYMENT_CASH, movement_type=CashMovement.TYPE_INCOME)), ZERO_MONEY),
        cash_expense=Coalesce(Sum('amount', filter=Q(payment_method=CashMovement.PAYMENT_CASH, movement_type=CashMovement.TYPE_EXPENSE)), ZERO_MONEY),
        card_total=Coalesce(Sum('amount', filter=Q(payment_method=CashMovement.PAYMENT_CARD, movement_type__in=SALE_TYPES)), ZERO_MONEY),
        digital_total=Coalesce(Sum('amount', filter=Q(payment_method=CashMovement.PAYMENT_QR, movement_type__in=SALE_TYPES)), ZERO_MONEY),
        income_total=Coalesce(Sum('amount', filter=Q(movement_type='INCOME')), ZERO_MONEY),
        expense_total=Coalesce(Sum('amount', filter=Q(movement_type='EXPENSE')), ZERO_MONEY),
        sales_total=Coalesce(Sum('amount', filter=Q(movement_type__in=SALE_TYPES)), ZERO_MONEY),
        tax_total=Coalesce(Sum('order__tax', filter=Q(movement_type__in=SALE_TYPES)), ZERO_MONEY),
    )
    expected_cash = session.opening_amount + totals['cash_sales'] + totals['cash_income'] - totals['cash_expense']

    return {
        'cash_total': totals['cash_sales'],
        'card_total': totals['card_total'],
        'digital_total': totals['digital_total'],
        'qr_total': totals['digital_total'],
        'expected_total': expected_cash,
        'expected_cash': expected_cash,
        'income_total': totals['income_total'],
        'income_cash': totals['cash_income'],
        'expense_total': totals['expense_total'],
        'expense_cash': totals['cash_expense'],
        'sales_total': totals['sales_total'],
        'tax_total': totals['tax_total'],
        'tips_total': Decimal('0'),
        'opening_amount': session.opening_amount,
    }


def record_order_payment(order, user):
    session = get_open_session(order.restaurant)

    if not session:
        raise CashRegisterClosedError('Debes abrir caja antes de registrar pagos')

    movement, _created = CashMovement.objects.get_or_create(
        order=order,
        defaults={
            'restaurant': order.restaurant,
            'session': session,
            'user': user,
            'movement_type': CashMovement.TYPE_SALE,
            'payment_method': order.payment_method or CashMovement.PAYMENT_CASH,
            'amount': order.total,
            'note': f'Pago orden #{order.id}',
        },
    )

    return movement
