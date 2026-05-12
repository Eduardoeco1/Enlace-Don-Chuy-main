from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from Sucursales.models import Sucursal
from decimal import Decimal

User = get_user_model()

class CierreCaja(models.Model):
    TURNO_CHOICES = [
        ('matutino',   'Turno Matutino'),
        ('vespertino', 'Turno Vespertino'),
        ('nocturno',   'Turno Nocturno'),
    ]

    usuario         = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    sucursal        = models.ForeignKey(
        Sucursal,
        on_delete    = models.CASCADE,
        related_name = 'cortes_caja',
        null         = True,
        verbose_name = 'Sucursal',
    )
    turno           = models.CharField(max_length=20, choices=TURNO_CHOICES, default='matutino')
    fecha           = models.DateField(auto_now_add=True)
    hora_cierre     = models.TimeField(auto_now_add=True)
    fondo_inicial   = models.DecimalField(max_digits=10, decimal_places=2, default=200.00)
    ventas_efectivo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    ventas_tarjeta  = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    ventas_delivery = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    efectivo_real   = models.DecimalField(max_digits=10, decimal_places=2)

    # Billetes MXN vigentes
    billetes_1000 = models.PositiveIntegerField(default=0, verbose_name='Billetes $1000')
    billetes_500  = models.PositiveIntegerField(default=0, verbose_name='Billetes $500')
    billetes_200  = models.PositiveIntegerField(default=0, verbose_name='Billetes $200')
    billetes_100  = models.PositiveIntegerField(default=0, verbose_name='Billetes $100')
    billetes_50   = models.PositiveIntegerField(default=0, verbose_name='Billetes $50')
    billetes_20   = models.PositiveIntegerField(default=0, verbose_name='Billetes $20')

    # Monedas MXN vigentes
    monedas_10    = models.PositiveIntegerField(default=0, verbose_name='Monedas $10')
    monedas_5     = models.PositiveIntegerField(default=0, verbose_name='Monedas $5')
    monedas_2     = models.PositiveIntegerField(default=0, verbose_name='Monedas $2')
    monedas_1     = models.PositiveIntegerField(default=0, verbose_name='Monedas $1')

    total_esperado  = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    diferencia      = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notas           = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name        = 'Corte de Caja'
        verbose_name_plural = 'Cortes de Caja'
        ordering            = ['-fecha', '-hora_cierre']

    def calcular_total_esperado(self):
        return Decimal(str(self.fondo_inicial)) + Decimal(str(self.ventas_efectivo))

    def calcular_diferencia(self):
        return Decimal(str(self.efectivo_real)) - self.calcular_total_esperado()

    def save(self, *args, **kwargs):
        self.total_esperado = self.calcular_total_esperado()
        self.diferencia     = self.calcular_diferencia()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Corte {self.fecha} — {self.sucursal} — {self.get_turno_display()}"


class ActividadTurno(models.Model):
    TIPO_CHOICES = [
        ('entrada',    'Entrada de Inventario'),
        ('retiro',     'Retiro de Caja'),
        ('validacion', 'Validación de Stock'),
        ('otro',       'Otro'),
    ]

    corte       = models.ForeignKey(CierreCaja, on_delete=models.CASCADE,
                                    related_name='actividades', null=True, blank=True)
    tipo        = models.CharField(max_length=20, choices=TIPO_CHOICES, default='otro')
    descripcion = models.CharField(max_length=255)
    hora        = models.TimeField(auto_now_add=True)
    fecha       = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_tipo_display()} — {self.descripcion}"
    

    