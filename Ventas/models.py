from django.db import models
from django.utils import timezone
from Sucursales.models import Sucursal
from Inventario.models import Producto as ProductoInventario

class Categoria(models.Model):
    nombre = models.CharField(max_length=100)
    icono  = models.CharField(max_length=50, default='restaurant_menu')
    orden  = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['orden']

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    categoria   = models.ForeignKey(Categoria, on_delete=models.SET_NULL,
                                    null=True, related_name='productos')
    sucursal    = models.ForeignKey(
        Sucursal,
        on_delete    = models.CASCADE,
        related_name = 'productos_venta',
        verbose_name = 'Sucursal',
        null         = True,
        blank        = True,
    )
    nombre      = models.CharField(max_length=200)
    descripcion = models.CharField(max_length=255, blank=True)
    precio      = models.DecimalField(max_digits=10, decimal_places=2)
    imagen      = models.ImageField(upload_to='ventas/productos/', blank=True, null=True)
    imagen_url  = models.URLField(blank=True, null=True)
    stock       = models.PositiveIntegerField(default=100)
    activo      = models.BooleanField(default=True)

    class Meta:
        ordering = ['categoria', 'nombre']

    def get_imagen(self):
        if self.imagen and hasattr(self.imagen, 'url'):
            return self.imagen.url
        if self.imagen_url:
            return self.imagen_url
        return f'https://placehold.co/300x200/f0eded/904800?text={self.nombre[0]}'

    def __str__(self):
        return f"{self.nombre} — ${self.precio}"


class Pedido(models.Model):
    TIPO_CHOICES = [
        ('mesa',     'En Mesa'),
        ('llevar',   'Para Llevar'),
        ('delivery', 'Delivery'),
    ]
    ESTADO_CHOICES = [
        ('abierto',   'Abierto'),
        ('procesado', 'Procesado'),
        ('cancelado', 'Cancelado'),
    ]

    ticket    = models.CharField(max_length=20, unique=True)
    sucursal  = models.ForeignKey(
        Sucursal,
        on_delete    = models.CASCADE,
        related_name = 'pedidos',
        null         = True,
        verbose_name = 'Sucursal',
    )
    tipo      = models.CharField(max_length=20, choices=TIPO_CHOICES, default='llevar')
    estado    = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='abierto')
    subtotal  = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total     = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    creado_en = models.DateTimeField(default=timezone.now)
    cajero    = models.ForeignKey('Sucursales.Usuario', on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name='pedidos')

    class Meta:
        ordering = ['-creado_en']

    def __str__(self):
        return f"Pedido {self.ticket} — ${self.total}"


class DetallePedido(models.Model):
    pedido   = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(
        ProductoInventario, 
        on_delete=models.PROTECT, 
        verbose_name='Producto'
    )
    cantidad = models.PositiveIntegerField(default=1)
    precio_u = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    notas    = models.CharField(max_length=255, blank=True)

    def save(self, *args, **kwargs):
        self.subtotal = self.precio_u * self.cantidad
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.cantidad}x {self.producto.nombre}"
    
    