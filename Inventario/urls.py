from django.urls import path
from . import views

app_name = 'Inventario'

urlpatterns = [
    path('', views.inventario_view, name='inventario'),
    path('exportar/', views.exportar_inventario, name='exportar'),
    path('producto/<int:producto_id>/editar/', views.editar_producto, name='editar_producto'),
    path('producto/<int:producto_id>/precio/', views.actualizar_precio_rapido, name='actualizar_precio'),
]

