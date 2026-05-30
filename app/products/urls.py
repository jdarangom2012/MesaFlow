from django.urls import path

from .views import category_create, category_update, category_toggle, categories_dashboard


app_name = 'products'

urlpatterns = [
    path('', categories_dashboard, name='categories'),
    path('create/', category_create, name='category_create'),
    path('<int:category_id>/update/', category_update, name='category_update'),
    path('<int:category_id>/toggle/', category_toggle, name='category_toggle'),
]
