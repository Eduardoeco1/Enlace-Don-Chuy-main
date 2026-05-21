from django.urls import path
from . import views

app_name = 'Sucursales'

urlpatterns = [
    # CORRECCIÓN: Sincronizado el name con el fetch AJAX de base.html (Línea 392)
    path('cambiar-sucursal/', views.cambiar_sucursal_global, name='cambiar_sucursal_global'),
]