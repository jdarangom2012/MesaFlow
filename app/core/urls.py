from django.urls import path
from .views import home, dashboard, pos

urlpatterns = [
    path('', home, name='home'),
    path('dashboard/', dashboard, name='dashboard'),
    path('pos/', pos, name='pos'),

]