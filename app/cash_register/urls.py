from django.urls import path

from .views import cash_register_dashboard, export_cash_register_excel, export_cash_register_pdf


app_name = 'cash_register'

urlpatterns = [
    path('', cash_register_dashboard, name='dashboard'),
    path('<int:session_id>/export/excel/', export_cash_register_excel, name='export_excel'),
    path('<int:session_id>/export/pdf/', export_cash_register_pdf, name='export_pdf'),
]
