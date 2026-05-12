from django.urls import path
from . import views

app_name = 'EntradaMercancia'

urlpatterns = [
    path('', views.entrada_mercancia_view, name='entrada'),
]
