from django.db import models
from django.contrib.auth import get_user_model
from Sucursales.models import Sucursal
from decimal import Decimal

User = get_user_model()


class CierreCaja(models.Model):
    TURNO_CHOICES = [
        ('matutino', 'Turno Matutino'),
        ('vespertino', 'Turno Vespertino'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    sucursal = models.ForeignKey(
        Sucursal,
        on_delete=models.CASCADE,
        related_name='cortes_caja',
        null=True,
        verbose_name='Sucursal',
    )

    turno = models.CharField(max_length=20, choices=TURNO_CHOICES, default='matutino')
    fecha = models.DateField(auto_now_add=True)
    hora_cierre = models.TimeField(auto_now_add=True)

    ventas_efectivo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    ventas_tarjeta = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    efectivo_real = models.DecimalField(max_digits=10, decimal_places=2)

    notas = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = 'Corte de Caja'
        verbose_name_plural = 'Cortes de Caja'
        ordering = ['-fecha', '-hora_cierre']

    def save(self, *args, **kwargs):
        self.ventas_efectivo = Decimal(str(self.ventas_efectivo or 0))
        self.ventas_tarjeta = Decimal(str(self.ventas_tarjeta or 0))
        self.efectivo_real = Decimal(str(self.efectivo_real or 0))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Corte {self.fecha} — {self.sucursal} — {self.get_turno_display()}"


class ActividadTurno(models.Model):
    TIPO_CHOICES = [
        ('entrada', 'Entrada de Inventario'),
        ('retiro', 'Retiro de Caja'),
        ('validacion', 'Validación de Stock'),
        ('otro', 'Otro'),
    ]

    corte = models.ForeignKey(
        CierreCaja,
        on_delete=models.CASCADE,
        related_name='actividades',
        null=True,
        blank=True
    )

    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='otro')
    descripcion = models.CharField(max_length=255)
    hora = models.TimeField(auto_now_add=True)
    fecha = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_tipo_display()} — {self.descripcion}"
    
    