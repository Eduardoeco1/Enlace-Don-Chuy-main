"""
Señales para sincronizar EntradaMercancia con Inventario.
Usa get_or_create para evitar duplicados.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import EntradaInsumo
from Inventario.models import Producto, Categoria


@receiver(post_save, sender=EntradaInsumo)
def actualizar_inventario_desde_entrada(sender, instance, created, **kwargs):
    """
    Al registrar entrada de mercancía:
    1. Busca producto existente en inventario (get_or_create)
    2. Si existe: suma al stock
    3. Si no existe: lo crea
    """
    if created and not instance.sincronizado:
        try:
            # Obtener o crear la categoría
            nombre_categoria = instance.get_categoria_inventario()
            categoria, _ = Categoria.objects.get_or_create(nombre=nombre_categoria)
            
            # USAR GET_OR_CREATE PARA EVITAR DUPLICADOS
            producto, created_producto = Producto.objects.get_or_create(
                nombre__iexact=instance.producto.strip(),
                sucursal=instance.sucursal,
                defaults={
                    'nombre': instance.producto.strip(),
                    'categoria': categoria,
                    'stock': instance.cantidad,
                    'unidad': instance.unidad,
                    'stock_minimo': 10,
                    'precio': 0,
                    'activo': True
                }
            )
            
            if not created_producto:
                # Si ya existía, SUMAR al stock en lugar de reemplazar
                producto.stock += instance.cantidad
                producto.categoria = categoria
                producto.unidad = instance.unidad
                producto.activo = True
                producto.save()
                
                import logging
                logger = logging.getLogger(__name__)
                logger.info(
                    f"✓ Stock actualizado: {producto.nombre} - "
                    f"Nuevo stock: {producto.stock} {producto.unidad}"
                )
            else:
                import logging
                logger = logging.getLogger(__name__)
                logger.info(
                    f"✓ Producto creado: {producto.nombre} - "
                    f"Stock inicial: {producto.stock} {producto.unidad}"
                )
            
            # Marcar como sincronizado
            EntradaInsumo.objects.filter(pk=instance.pk).update(sincronizado=True)
                
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"✗ Error al sincronizar inventario: {e}")

            