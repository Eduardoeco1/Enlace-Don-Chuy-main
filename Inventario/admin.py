from django.contrib import admin
from .models import Producto, Categoria, Sucursal

#@admin.register(Sucursal)
class SucursalAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'clave', 'activa')

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre',)

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display  = ('nombre', 'categoria', 'sucursal', 'stock', 'unidad', 'stock_minimo', 'activo')
    list_filter   = ('sucursal', 'categoria', 'activo')
    search_fields = ('nombre',)
    list_editable = ('stock', 'activo')

    fieldsets = (
        ('Información del Producto', {
            'fields': ('nombre', 'categoria', 'imagen')
        }),
        ('Stock', {
            'fields': ('stock', 'unidad', 'stock_minimo', 'sucursal')
        }),
        ('Estado', {
            'fields': ('activo',)
        }),
    )


    