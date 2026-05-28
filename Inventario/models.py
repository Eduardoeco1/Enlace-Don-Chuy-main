from decimal import Decimal
from django.db import models
from Sucursales.models import Sucursal


CATEGORIAS_FIJAS = [
    'Pollo/Partes de pollo',
    'Acompañamientos',
]


class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True, verbose_name='Categoría')

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

    @classmethod
    def inicializar_categorias(cls):
        for nombre_cat in CATEGORIAS_FIJAS:
            cls.objects.get_or_create(nombre=nombre_cat)


class Producto(models.Model):
    UNIDAD_CHOICES = [
        ('PZ', 'PZ - Pieza'),
        ('KG', 'KG - Kilogramos'),
        ('G', 'G - Gramos'),
        ('LT', 'LT - Litros'),
        ('ML', 'ML - Mililitros'),
        ('PAQ', 'PAQ - Paquete'),
        ('CJ', 'CJ - Caja'),
    ]

    nombre = models.CharField(max_length=200, verbose_name='Nombre')

    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Categoría'
    )

    sucursal = models.ForeignKey(
        Sucursal,
        on_delete=models.CASCADE,
        related_name='productos_inventario',
        verbose_name='Sucursal',
        null=True,
        blank=True
    )

    stock = models.DecimalField(
        max_digits=10,
        decimal_places=1,
        default=0,
        verbose_name='Stock actual'
    )

    unidad = models.CharField(
        max_length=20,
        choices=UNIDAD_CHOICES,
        default='PZ',
        verbose_name='Unidad'
    )

    stock_minimo = models.DecimalField(
        max_digits=10,
        decimal_places=1,
        default=10,
        verbose_name='Stock mínimo'
    )

    precio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Precio de venta',
        help_text='Precio unitario del producto'
    )

    imagen = models.ImageField(
        upload_to='inventario/',
        blank=True,
        null=True,
        verbose_name='Imagen'
    )

    activo = models.BooleanField(default=True, verbose_name='Activo')
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['nombre']

    def estado(self):
        if self.stock <= Decimal('0'):
            return 'agotado'
        elif self.stock <= self.stock_minimo * Decimal('0.3'):
            return 'critico'
        elif self.stock <= self.stock_minimo:
            return 'bajo'
        return 'optimo'

    def estado_display(self):
        estados = {
            'optimo': 'Óptimo',
            'bajo': 'Bajo',
            'critico': 'Crítico',
            'agotado': 'Agotado',
        }
        return estados.get(self.estado(), 'Óptimo')

    @property
    def imagen_url(self):
        if self.imagen:
            return self.imagen.url

        iniciales = self.nombre[:2].upper() if self.nombre else 'LC'
        return f'https://placehold.co/40x40/f0eded/904800?text={iniciales}'

    def get_imagen(self):
        if self.imagen:
            return self.imagen.url

        iniciales = self.nombre[:2].upper() if self.nombre else 'LC'
        return f'https://placehold.co/300x200/f0eded/904800?text={iniciales}'

    def __str__(self):
        sucursal = self.sucursal if self.sucursal else 'Sin Sucursal'
        return f'{self.nombre} — {sucursal}'
    
    