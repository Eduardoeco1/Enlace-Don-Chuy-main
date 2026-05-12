from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import DetalleVenta, MovimientoInventario

@receiver(post_save, sender=DetalleVenta)
def descontar_stock_al_vender(sender, instance, created, **kwargs):
    """
    Cada vez que se crea un DetalleVenta:
    1. Resta la cantidad del stock del Producto.
    2. Registra un MovimientoInventario tipo 'salida'.
    """
    if created:
        producto = instance.producto

        # 1. Descontar stock
        producto.stock = max(0, producto.stock - instance.cantidad)
        producto.save(update_fields=['stock'])

        # 2. Registrar movimiento
        MovimientoInventario.objects.create(
            producto=producto,
            cantidad=instance.cantidad,
            tipo='salida',
            nota=f'Venta automática — {instance.venta.referencia}'
        )
        