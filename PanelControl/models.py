from django.db import models
from django.utils import timezone

class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock  = models.PositiveIntegerField(default=0)
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)

    def __str__(self):
        return self.nombre

    def imagen_url(self):
        """Devuelve la URL de la imagen o un placeholder si no tiene."""
        if self.imagen and hasattr(self.imagen, 'url'):
            return self.imagen.url
        return 'https://placehold.co/48x48/f0eded/904800?text=LC'

class MovimientoInventario(models.Model):
    TIPO_CHOICES = [('entrada', 'Entrada'), ('salida', 'Salida (venta)')]
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    tipo     = models.CharField(max_length=10, choices=TIPO_CHOICES)
    fecha    = models.DateTimeField(default=timezone.now)
    nota     = models.TextField(blank=True)

    def __str__(self):
        return f"{self.tipo} - {self.producto.nombre} x{self.cantidad}"

class Venta(models.Model):
    fecha      = models.DateTimeField(default=timezone.now)
    total      = models.DecimalField(max_digits=10, decimal_places=2)
    referencia = models.CharField(max_length=20, blank=True)

    def save(self, *args, **kwargs):
        if not self.referencia:
            super().save(*args, **kwargs)
            self.referencia = f'#TX-{self.pk + 9000}'
            Venta.objects.filter(pk=self.pk).update(referencia=self.referencia)
        else:
            super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.referencia} — ${self.total}"

class DetalleVenta(models.Model):
    venta    = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.producto.nombre} x{self.cantidad}"

class SalidaCaja(models.Model):
    concepto = models.CharField(max_length=200)
    monto    = models.DecimalField(max_digits=10, decimal_places=2)
    fecha    = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.concepto} — ${self.monto}"
    