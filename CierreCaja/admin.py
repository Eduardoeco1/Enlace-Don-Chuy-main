from django.contrib import admin
from .models import CierreCaja, ActividadTurno


@admin.register(CierreCaja)
class CierreCajaAdmin(admin.ModelAdmin):
    list_display = (
        'fecha',
        'hora_cierre',
        'sucursal',
        'usuario',
        'turno',
        'ventas_efectivo',
        'ventas_tarjeta',
        'efectivo_real',
    )

    list_filter = (
        'fecha',
        'turno',
        'sucursal',
    )

    search_fields = (
        'usuario__username',
        'sucursal__nombre',
        'notas',
    )

    readonly_fields = (
        'fecha',
        'hora_cierre',
    )


@admin.register(ActividadTurno)
class ActividadTurnoAdmin(admin.ModelAdmin):
    list_display = (
        'fecha',
        'hora',
        'tipo',
        'descripcion',
    )

    list_filter = (
        'fecha',
        'tipo',
    )

    search_fields = (
        'descripcion',
    )



    