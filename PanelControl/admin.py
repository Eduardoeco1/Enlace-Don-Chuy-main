from django.contrib import admin
from .models import Producto, MovimientoInventario, Venta, DetalleVenta, SalidaCaja

admin.site.register(Producto)
admin.site.register(MovimientoInventario)
admin.site.register(Venta)
admin.site.register(DetalleVenta)
admin.site.register(SalidaCaja)