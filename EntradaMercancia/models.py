from django.db import models
from django.utils import timezone
from Sucursales.models import Sucursal

class EntradaInsumo(models.Model):
    SUCURSALES = [
        ('centro', 'Sucursal Principal - Centro'),
        ('norte',  'Sucursal Norte - Brasas'),
        ('sur',    'Sucursal Sur - Humo & Sal'),
    ]

    producto      = models.CharField(max_length=200, verbose_name='Producto')
    cantidad      = models.DecimalField(max_digits=10, decimal_places=2)
    unidad        = models.CharField(max_length=20, default='KG')
    fecha_entrada = models.DateField()
    sucursal      = models.ForeignKey(
        Sucursal,
        on_delete    = models.CASCADE,
        related_name = 'entradas_mercancia',
        verbose_name = 'Sucursal de Destino',
        null         = True,
    )
    notas      = models.TextField(blank=True, null=True)
    creado_en  = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name        = 'Entrada de Insumo'
        verbose_name_plural = 'Entradas de Insumos'
        ordering            = ['-creado_en']

    def __str__(self):
        return f"{self.producto} — {self.cantidad} {self.unidad}"
    
    