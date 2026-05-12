from django.contrib import admin
from .models import CierreCaja, ActividadTurno

class ActividadInline(admin.TabularInline):
    model  = ActividadTurno
    extra  = 0
    fields = ('tipo', 'descripcion', 'hora')
    readonly_fields = ('hora',)

@admin.register(CierreCaja)
class CierreCajaAdmin(admin.ModelAdmin):
    list_display    = ('fecha', 'turno', 'usuario', 'ventas_efectivo', 'efectivo_real', 'total_esperado', 'diferencia_coloreada', 'hora_cierre')
    list_filter     = ('turno', 'fecha', 'usuario')
    search_fields   = ('usuario__username', 'notas')
    readonly_fields = ('fecha', 'hora_cierre', 'total_esperado', 'diferencia')
    inlines         = [ActividadInline]

    fieldsets = (
        ('Información del Turno', {
            'fields': ('usuario', 'turno', 'fecha', 'hora_cierre')
        }),
        ('Ventas del Sistema', {
            'fields': ('fondo_inicial', 'ventas_efectivo', 'ventas_tarjeta', 'ventas_delivery')
        }),
        ('Declaración del Cajero', {
            'fields': ('efectivo_real', 'billetes_100', 'billetes_50', 'billetes_20', 'billetes_10')
        }),
        ('Resultado', {
            'fields': ('total_esperado', 'diferencia', 'notas'),
        }),
    )

    def diferencia_coloreada(self, obj):
        from django.utils.html import format_html
        color = 'green' if obj.diferencia >= 0 else 'red'
        signo = '+' if obj.diferencia > 0 else ''
        return format_html('<b style="color:{}">{}{}</b>', color, signo, obj.diferencia)
    diferencia_coloreada.short_description = 'Diferencia'

@admin.register(ActividadTurno)
class ActividadTurnoAdmin(admin.ModelAdmin):
    list_display = ('descripcion', 'tipo', 'hora', 'fecha')
    list_filter  = ('tipo', 'fecha')
    