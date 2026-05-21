from django.db import models
from Sucursales.models import Sucursal
from decimal import Decimal

# Categorías fijas del sistema
CATEGORIAS_FIJAS = [
    'Pollo/Partes de pollo',
    'Condimentos',
    'Acompañamientos',
]


class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True, verbose_name='Categoría')

    class Meta:
        verbose_name        = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering            = ['nombre']

    def __str__(self):
        return self.nombre
    
    @classmethod
    def inicializar_categorias(cls):
        """Crea las categorías fijas si no existen"""
        for nombre_cat in CATEGORIAS_FIJAS:
            cls.objects.get_or_create(nombre=nombre_cat)


class Producto(models.Model):
    ESTADO_CHOICES = [
        ('optimo',  'Óptimo'),
        ('bajo',    'Bajo'),
        ('critico', 'Crítico'),
        ('agotado', 'Agotado'),
    ]
    UNIDAD_CHOICES = [
        ('Kg',      'Kilogramos'),
        ('Lt',      'Litros'),
        ('Pza',     'Piezas'),
        ('Potes',   'Potes'),
        ('Bultos',  'Bultos'),
        ('Docenas', 'Docenas'),
    ]

    nombre       = models.CharField(max_length=200, verbose_name='Nombre')
    categoria    = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True)
    
    # Permitir null y blank temporalmente para que la migración no pida un default
    sucursal     = models.ForeignKey(
        Sucursal, 
        on_delete=models.CASCADE,
        related_name='productos_inventario',
        verbose_name='Sucursal',
        null=True, 
        blank=True
    )
    
    stock        = models.DecimalField(max_digits=10, decimal_places=1)
    unidad       = models.CharField(max_length=20, choices=UNIDAD_CHOICES, default='Kg')
    stock_minimo = models.DecimalField(max_digits=10, decimal_places=1, default=10)
    
    # Precio de Venta requerido por el negocio
    precio       = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0, 
        verbose_name='Precio de Venta',
        help_text='Precio unitario del producto'
    )
    
    imagen       = models.ImageField(upload_to='inventario/', blank=True, null=True)
    activo       = models.BooleanField(default=True)
    creado_en    = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Producto'
        verbose_name_plural = 'Productos'
        ordering            = ['nombre']

    def estado(self):
        if self.stock <= Decimal('0'):
            return 'agotado'
        elif self.stock <= self.stock_minimo * Decimal('0.3'):
            return 'critico'
        elif self.stock <= self.stock_minimo:
            return 'bajo'
        return 'optimo'

    def estado_display(self):
        return {'optimo': 'Óptimo', 'bajo': 'Bajo',
                'critico': 'Crítico', 'agotado': 'Agotado'}.get(self.estado(), 'Óptimo')

    def imagen_url(self):
        if self.imagen and hasattr(self.imagen, 'url'):
            return self.imagen.url
        return f'https://placehold.co/40x40/f0eded/904800?text={self.nombre[0]}'

    def get_imagen(self):
        """Devuelve la URL de la imagen o el placeholder requerido por la vista del panel."""
        if self.imagen and hasattr(self.imagen, 'url'):
            return self.imagen.url
        return f'https://placehold.co/48x48/f0eded/904800?text={self.nombre[:2].upper()}'

    def __str__(self):
        # Manejamos el caso de que la sucursal sea None para evitar errores en el admin
        return f"{self.nombre} — {self.sucursal if self.sucursal else 'Sin Sucursal'}"
    
    