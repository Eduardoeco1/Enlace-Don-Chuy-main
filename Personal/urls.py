from django.urls import path
from . import views

app_name = 'Personal'

urlpatterns = [
    # ─── Gestión de Personal ───────────────────────────────────
    # Listado principal, métricas y registro de empleados
    path('', views.personal_view, name='personal'),
    
    # Edición de datos (Sucursal, Rol, Usuario)
    path('editar/<int:empleado_id>/', views.editar_empleado_view, name='editar_empleado'),
    
    # Eliminación definitiva de cuenta y perfil
    path('eliminar/<int:empleado_id>/', views.eliminar_empleado_view, name='eliminar_empleado'),

    # ─── Control de Asistencia ────────────────────────────────
    # Vista para que el empleado marque entrada/salida/justificante
    path('asistencia/', views.marcar_asistencia, name='asistencia'),
    
    # Vista de tabla administrativa de asistencias (Gerente/Dueña)
    path('asistencias/', views.tabla_asistencias, name='asistencias'),

    path('',              views.personal_view,    name='personal'),
    path('asistencia/',   views.marcar_asistencia, name='asistencia'),   # empleado
    path('asistencias/',  views.tabla_asistencias,  name='asistencias'), # admin



]

#
