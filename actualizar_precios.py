# Script para poner precio por defecto a productos sin precio
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'enlacechuy.settings')
django.setup()

from Inventario.models import Producto
from decimal import Decimal

productos = Producto.objects.filter(precio=0)
print(f"Productos sin precio: {productos.count()}")

for p in productos:
    p.precio = Decimal('50.00')  # Precio por defecto
    p.save()
    print(f"✓ {p.nombre} - Precio actualizado a $50.00")

print("¡Listo!")





