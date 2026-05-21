from django.contrib import admin
from .models import Empleado, Turno, Asistencia, Justificante

@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display  = ('nombre_completo', 'rol', 'sucursal', 'estado', 'en_turno', 'creado_en')
    list_filter   = ('rol', 'sucursal', 'estado', 'en_turno')
    search_fields = ('usuario__first_name', 'usuario__last_name', 'usuario__email')
    list_editable = ('estado', 'en_turno')

@admin.register(Turno)
class TurnoAdmin(admin.ModelAdmin):
    list_display  = ('empleado', 'fecha', 'tipo_turno', 'hora_inicio', 'hora_fin', 'creado_en')
    list_filter   = ('fecha', 'tipo_turno', 'empleado__sucursal')
    search_fields = ('empleado__usuario__first_name', 'empleado__usuario__last_name', 'notas')
 

