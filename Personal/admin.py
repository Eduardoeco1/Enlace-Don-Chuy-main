from django.contrib import admin
from .models import Empleado, Turno

@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    # CORRECCIÓN: Se cambió 'fecha_alta' por 'creado_en' para coincidir con el modelo
    list_display  = ('nombre_completo', 'rol', 'sucursal', 'estado', 'en_turno', 'creado_en')
    list_filter   = ('rol', 'sucursal', 'estado', 'en_turno')
    search_fields = ('usuario__first_name', 'usuario__last_name', 'usuario__email')
    list_editable = ('estado', 'en_turno')

@admin.register(Turno)
class TurnoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'sucursal', 'fecha', 'hora_inicio', 'hora_fin')
    list_filter  = ('sucursal', 'fecha')
    filter_horizontal = ('personal',)

    
    