from django.contrib import admin
from .models import Sucursal, MetaSemanal, CierreCaja, Insumo

@admin.register(Sucursal)
class SucursalAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'activa')

@admin.register(MetaSemanal)
class MetaSemanalAdmin(admin.ModelAdmin):
    list_display = ('objetivo_monto', 'fecha_inicio', 'sucursal')

@admin.register(CierreCaja)
class CierreCajaAdmin(admin.ModelAdmin):
    list_display  = ('fecha', 'turno', 'responsable', 'monto_total', 'diferencia', 'sucursal')
    list_filter   = ('turno', 'fecha', 'sucursal')
    search_fields = ('responsable__username',)

@admin.register(Insumo)
class InsumoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'stock_esperado', 'stock_fisico', 'unidad', 'costo_diferencia', 'sucursal')
    list_filter  = ('sucursal',)


    