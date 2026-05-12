from django.db import models
# CORRECCIÓN: Importar settings para referenciar el modelo de usuario activo
from django.conf import settings
from django.utils import timezone

class Sucursal(models.Model):
    nombre    = models.CharField(max_length=100, verbose_name='Nombre')
    direccion = models.TextField(blank=True, verbose_name='Dirección')
    activa    = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Sucursal'
        verbose_name_plural = 'Sucursales'

    def __str__(self):
        return self.nombre

class MetaSemanal(models.Model):
    objetivo_monto = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Objetivo ($)')
    fecha_inicio   = models.DateField(verbose_name='Inicio de Semana')
    sucursal       = models.ForeignKey(Sucursal, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = 'Meta Semanal'
        verbose_name_plural = 'Metas Semanales'
        ordering = ['-fecha_inicio']

    def __str__(self):
        return f"Meta ${self.objetivo_monto} — semana del {self.fecha_inicio}"

class CierreCaja(models.Model):
    TURNO_CHOICES = [
        ('matutino',   'Turno Matutino'),
        ('vespertino', 'Turno Vespertino'),
        ('nocturno',   'Turno Nocturno'),
    ]
    
    # CORRECCIÓN: Cambiar 'User' por 'settings.AUTH_USER_MODEL'
    # Se mantiene related_name para evitar conflictos de acceso inverso
    responsable    = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        verbose_name='Responsable',
        related_name='reportes_caja'
    )
    turno           = models.CharField(max_length=20, choices=TURNO_CHOICES)
    fecha           = models.DateField(default=timezone.now)
    monto_total    = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Monto Total')
    diferencia      = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Diferencia')
    sucursal        = models.ForeignKey(Sucursal, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = 'Cierre de Caja'
        verbose_name_plural = 'Cierres de Caja'
        ordering = ['-fecha']

    def __str__(self):
        nombre = self.responsable.get_full_name() if self.responsable else 'Sin responsable'
        return f"{self.fecha} — {self.get_turno_display()} — {nombre}"

class Insumo(models.Model):
    nombre          = models.CharField(max_length=150, verbose_name='Insumo')
    unidad          = models.CharField(max_length=30, default='kg', verbose_name='Unidad')
    stock_esperado  = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Stock Teórico')
    stock_fisico    = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Stock Real')
    costo_diferencia= models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Costo Estimado')
    sucursal        = models.ForeignKey(Sucursal, on_delete=models.SET_NULL, null=True, blank=True)
    icono           = models.CharField(max_length=50, default='inventory_2', verbose_name='Ícono Material')

    class Meta:
        verbose_name = 'Insumo'
        verbose_name_plural = 'Insumos'

    def diferencia(self):
        return self.stock_fisico - self.stock_esperado

    def __str__(self):
        return f"{self.nombre} — Real: {self.stock_fisico} / Esperado: {self.stock_esperado} {self.unidad}"
    

    