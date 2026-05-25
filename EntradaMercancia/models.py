from django.db import models
from django.utils import timezone
from Sucursales.models import Sucursal

class EntradaInsumo(models.Model):
    """
    Modelo para registrar entradas de mercancía.
    Incluye un catálogo fijo de productos en un dropdown y categoría 
    para sincronización limpia con Inventario.
    """
    
    # Catálogo de Insumos Fijos para el Dropdown (Segúna catálogo visual de Enlace Don Chuy)
    PRODUCTOS_CHOICES = [
        ('Pollo', 'Pollo'),
        ('Cabeza', 'Cabeza'),
        ('Patita', 'Patita'),
        ('Alitas', 'Alitas'),
        ('Salchica', 'Salchica'),
        ('Tacos', 'Tacos'),
        ('Arroz', 'Arroz'),
        ('Chiltepin', 'Chiltepin'),
        ('Salsas', 'Salsas'),
        ('Chile en polvo sasonador', 'Chile en polvo sasonador'),
        ('Chile en polvo', 'Chile en polvo'),
        ('Condimento', 'Condimento'),
    ]
    
    # Categorías fijas (iguales a las de Inventario)
    CATEGORIAS = [
        ('pollo', 'Pollo/Partes de pollo'),
        ('condimentos', 'Condimentos'),
        ('acompañamientos', 'Acompañamientos'),
    ]

    producto = models.CharField(
        max_length=200, 
        choices=PRODUCTOS_CHOICES,
        default='Pollo',
        verbose_name='Producto'
    )
    categoria = models.CharField(
        max_length=50,
        choices=CATEGORIAS,
        default='pollo',
        verbose_name='Categoría',
        help_text='Categoría del producto para clasificación'
    )
    cantidad = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name='Cantidad'
    )
    unidad = models.CharField(
        max_length=20, 
        default='KG',
        verbose_name='Unidad de Medida'
    )
    fecha_entrada = models.DateField(
        verbose_name='Fecha de Entrada'
    )
    sucursal = models.ForeignKey(
        Sucursal,
        on_delete    = models.CASCADE,
        related_name = 'entradas_mercancia',
        verbose_name = 'Sucursal de Destino',
    )
    notas = models.TextField(
        blank=True, 
        null=True,
        verbose_name='Notas Adicionales'
    )
    creado_en = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de Registro'
    )
    
    # Campo para rastrear si se sincronizó con inventario
    sincronizado = models.BooleanField(
        default=False,
        verbose_name='Sincronizado con Inventario'
    )

    class Meta:
        verbose_name        = 'Entrada de Insumo'
        verbose_name_plural = 'Entradas de Insumos'
        ordering            = ['-creado_en']

    def __str__(self):
        return f"{self.get_producto_display()} — {self.cantidad} {self.unidad} ({self.get_categoria_display()})"
    
    def get_categoria_inventario(self):
        """Retorna el nombre de la categoría para sincronizar con Inventario"""
        mapping = {
            'pollo': 'Pollo/Partes de pollo',
            'condimentos': 'Condimentos',
            'acompañamientos': 'Acompañamientos',
        }
        return mapping.get(self.categoria, 'Pollo/Partes de pollo')
    
    