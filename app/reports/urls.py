from django.urls import path

from .views import export_reports_excel, export_reports_pdf, reports_dashboard


app_name = 'reports'

urlpatterns = [
    path('', reports_dashboard, name='dashboard'),
    path('export/excel/', export_reports_excel, name='export_excel'),
    path('export/pdf/', export_reports_pdf, name='export_pdf'),
]
