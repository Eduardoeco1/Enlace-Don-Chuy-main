import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'enlacechuy.settings')
django.setup()

from Inventario.models import Producto
from django.db.models import Count

# Encontrar duplicados
duplicados = Producto.objects.values('nombre', 'sucursal').annotate(
    count=Count('id')
).filter(count__gt=1)

print(f"Encontrados {duplicados.count()} productos duplicados")

for dup in duplicados:
    productos = Producto.objects.filter(
        nombre=dup['nombre'],
        sucursal_id=dup['sucursal']
    ).order_by('id')
    
    # Mantener el primero, sumar stocks, eliminar duplicados
    principal = productos.first()
    stock_total = sum(p.stock for p in productos)
    
    print(f"\n{principal.nombre} - {principal.sucursal.nombre}")
    print(f"  Stock total: {stock_total}")
    
    principal.stock = stock_total
    principal.save()
    
 # === AQUÍ ESTÁ EL CAMBIO IMPORTANTE ===
    # 1. Buscar todos los duplicados que NO sean el principal
    duplicados_a_eliminar = productos.exclude(id=principal.id)
    
    # 2. Reasignar los detalles de pedidos de los duplicados al producto principal
    # (Suponiendo que la relación en DetallePedido se llama 'detallepedido_set')
    for dup in duplicados_a_eliminar:
        # Esto busca los detalles vinculados a este duplicado y los pasa al principal
        dup.detallepedido_set.all().update(producto=principal)
    
    # 3. Ahora que nadie los referencia, ya los podemos borrar sin peligro
    duplicados_a_eliminar.delete()
    print("  ✓ Duplicados eliminados y pedidos reasignados")



    
