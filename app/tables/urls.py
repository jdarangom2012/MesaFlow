from django.urls import path

from .views import close_table, release_table, table_create, table_delete, table_edit, tables_dashboard


urlpatterns = [
    path('', tables_dashboard, name='tables_dashboard'),
    path('create/', table_create, name='table_create'),
    path('<int:table_id>/edit/', table_edit, name='table_edit'),
    path('<int:table_id>/delete/', table_delete, name='table_delete'),
    path('<int:table_id>/close/', close_table, name='close_table'),
    path('<int:table_id>/release/', release_table, name='release_table'),
]
