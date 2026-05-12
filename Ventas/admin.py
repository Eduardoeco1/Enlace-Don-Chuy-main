from django.contrib import admin
from .models import Categoria, Producto, Pedido, DetallePedido

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'icono', 'orden')
    list_editable = ('orden',)

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display  = ('nombre', 'categoria', 'precio', 'stock', 'activo')
    list_filter   = ('categoria', 'activo')
    search_fields = ('nombre',)
    list_editable = ('precio', 'stock', 'activo')

class DetalleInline(admin.TabularInline):
    model  = DetallePedido
    extra  = 0
    fields = ('producto', 'cantidad', 'precio_u', 'subtotal')
    readonly_fields = ('subtotal',)

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display  = ('ticket', 'tipo', 'estado', 'subtotal', 'iva', 'total', 'creado_en')
    list_filter   = ('estado', 'tipo')
    inlines       = [DetalleInline]
    readonly_fields = ('ticket', 'subtotal', 'iva', 'total')


    