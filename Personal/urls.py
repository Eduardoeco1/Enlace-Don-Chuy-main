from django.urls import path
from . import views

app_name = 'Personal'

urlpatterns = [
    # ─── Gestión de Personal ───
    # Listado principal, métricas y registro de empleados
    path('', views.personal_view, name='personal'),
    
    # Edición de datos (Sucursal, Rol, Usuario)
    path('editar/<int:empleado_id>/', views.editar_empleado_view, name='editar_empleado'),
    
    # Eliminación definitiva de cuenta y perfil
    path('eliminar/<int:empleado_id>/', views.eliminar_empleado_view, name='eliminar_empleado'),
    
    # Creador y editor de turnos operativos (Problema 8)
    path('guardar-turno/', views.guardar_turno, name='guardar_turno'),

    # ─── Control de Asistencia ───
    # Vista para que el empleado marque entrada/salida/justificante
    path('asistencia/', views.marcar_asistencia, name='asistencia'),
    
    # Vista de tabla administrativa de asistencias (Gerente/Dueña)
    path('asistencias/', views.tabla_asistencias, name='asistencias'),
    
    # ─── Gestión de Justificantes ───
    path('justificantes/', views.subir_justificante, name='justificantes'),
    path('mis-justificantes/', views.mis_justificantes, name='mis_justificantes'),
    path('control-justificantes/', views.control_justificantes, name='control_justificantes'),
    path('revisar-justificante/<int:justificante_id>/', views.revisar_justificante, name='revisar_justificante'),
]







