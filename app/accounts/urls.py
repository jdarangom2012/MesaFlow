from django.urls import path

from .views import MesaFlowLoginView, logout_view

urlpatterns = [
    path('login/', MesaFlowLoginView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),
]
