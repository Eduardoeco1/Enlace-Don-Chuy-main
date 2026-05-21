from django.db import models
from django.conf import settings
from django.utils import timezone

class Notificacion(models.Model):
    """Sistema de notificaciones internas"""
    TIPO_CHOICES = [
        ('info', 'Información'),
        ('success', 'Éxito'),
        ('warning', 'Advertencia'),
        ('error', 'Error'),
        ('justificante', 'Justificante'),
    ]
    
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notificaciones'
    )
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='info')
    titulo = models.CharField(max_length=200)
    mensaje = models.TextField()
    leida = models.BooleanField(default=False)
    url_accion = models.CharField(max_length=500, blank=True)
    creada_en = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-creada_en']
        
    def __str__(self):
        return f"{self.usuario.username} - {self.titulo}"

    @classmethod
    def create_notificacion(cls, usuario, titulo, tipo='info', mensaje='', **kwargs):
        """
        Método alternativo de creación robusto. 
        Soporta y procesa argumentos antiguos (sucursal, detalle, icono, color, url) 
        evitando lanzar un TypeError.
        """
        # Remapear 'detalle' a 'mensaje' si viene vacío
        if not mensaje and 'detalle' in kwargs:
            mensaje = kwargs.pop('detalle')
            
        # Remapear 'url' a 'url_accion' si existe
        url_accion = kwargs.pop('url', '') if 'url_accion' not in kwargs else kwargs.get('url_accion', '')
        
        # Consumir el resto de parámetros viejos que causan error para limpiarlos
        kwargs.pop('sucursal', None)
        kwargs.pop('icono', None)
        kwargs.pop('color', None)
        
        # Crear la instancia de forma segura usando únicamente los campos válidos del modelo
        return cls.objects.create(
            usuario=usuario,
            titulo=titulo,
            tipo=tipo,
            mensaje=mensaje,
            url_accion=url_accion,
            **kwargs
        )
    








    