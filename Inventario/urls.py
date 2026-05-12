from django.urls import path
from . import views

app_name = 'Inventario'

urlpatterns = [
    path('', views.inventario_view, name='inventario'),
    path('exportar/', views.exportar_inventario, name='exportar'),

]

