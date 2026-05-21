from django.urls import path
from . import views

app_name = 'Perfil'

urlpatterns = [
    # Cambiado views.ver_perfil por views.perfil_view que es tu función real
    path('', views.perfil_view, name='perfil'),
    
    # Esta ruta procesa tu formulario de edición
    path('editar/', views.editar_perfil, name='editar_perfil'),
]

