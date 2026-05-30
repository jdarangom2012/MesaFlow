from django.urls import path

from .views import confirm_payment, payments_dashboard


app_name = 'payments'

urlpatterns = [
    path('', payments_dashboard, name='dashboard'),
    path('<int:order_id>/pay/', confirm_payment, name='confirm_payment'),
]
