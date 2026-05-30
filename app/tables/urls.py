from django.urls import path

from .views import close_table, release_table, tables_dashboard


urlpatterns = [
    path('', tables_dashboard, name='tables_dashboard'),
    path('<int:table_id>/close/', close_table, name='close_table'),
    path('<int:table_id>/release/', release_table, name='release_table'),
]
