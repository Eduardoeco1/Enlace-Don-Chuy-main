from django.urls import path
from . import views

app_name = 'Sucursales'

urlpatterns = [
    path('cambiar-sucursal/', views.cambiar_sucursal, name='cambiar_sucursal'),
]

