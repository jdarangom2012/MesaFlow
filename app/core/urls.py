from django.urls import path
from .views import home, dashboard, pos, qr_menu
from kitchen.views import kitchen_display

urlpatterns = [
    path('', home, name='home'),
    path('dashboard/', dashboard, name='dashboard'),
    path('pos/', pos, name='pos'),
    path('kitchen/', kitchen_display, name='kitchen'),
    path('menu/<int:table_id>/', qr_menu, name='qr_menu'),

]
