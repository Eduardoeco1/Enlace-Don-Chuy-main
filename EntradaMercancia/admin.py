from django.contrib import admin
from .models import EntradaInsumo

@admin.register(EntradaInsumo)
class EntradaInsumoAdmin(admin.ModelAdmin):
    list_display    = ('producto', 'cantidad', 'unidad', 'sucursal', 'fecha_entrada', 'creado_en')
    list_filter     = ('sucursal', 'fecha_entrada', 'producto')
    search_fields   = ('producto', 'notas')
    ordering        = ('-creado_en',)
    readonly_fields = ('creado_en',)

    fieldsets = (
        ('Datos del Insumo', {
            'fields': ('producto', 'cantidad', 'unidad')
        }),
        ('Destino y Fecha', {
            'fields': ('sucursal', 'fecha_entrada')
        }),
        ('Observaciones', {
            'fields': ('notas',)
        }),
        ('Registro', {
            'fields': ('creado_en',),
            'classes': ('collapse',),
        }),
    )
    