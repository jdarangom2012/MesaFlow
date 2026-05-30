from django.urls import path
from .views import dashboard, dashboard_data, home, pos, qr_menu
from kitchen.views import kitchen_display, kitchen_orders_partial

urlpatterns = [
    path('', home, name='home'),
    path('dashboard/', dashboard, name='dashboard'),
    path('dashboard/data/', dashboard_data, name='dashboard_data'),
    path('pos/', pos, name='pos'),
    path('kitchen/', kitchen_display, name='kitchen'),
    path('kitchen/orders/', kitchen_orders_partial, name='kitchen_orders_partial'),
    path('menu/<int:table_id>/', qr_menu, name='qr_menu'),

]
