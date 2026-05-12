from django.urls import path
from . import views

app_name = 'Ventas'

urlpatterns = [
    path('',              views.pos_view,       name='Ventas'),
    path('procesar/',     views.procesar_venta, name='procesar'),
]


