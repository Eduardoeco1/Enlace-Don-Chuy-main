import os
from django.db import models
from django.conf import settings
from django.utils import timezone  # Añadido para el default de fecha en Asistencia
from Inventario.models import Sucursal

class Empleado(models.Model):
    """
    Modelo principal para la gestión de personal en el sistema multisucursal.
    """
    # Definición de Roles fijos para el sistema
    ROLES_CHOICES = [
        ('gerente', 'Gerente'),
        ('empleado', 'Empleado'),
    ]

    # Estados operativos del personal
    ESTADO_CHOICES = [
        ('activo',   'Activo'),
        ('descanso', 'En Descanso'),
        ('offline',  'Offline'),
    ]

    # Vínculo con el sistema de autenticación de Django
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='empleado'
    )
    
    # El campo 'rol' ahora es directo, lo que facilita los decoradores de permisos
    rol = models.CharField(
        max_length=20, 
        choices=ROLES_CHOICES, 
        default='empleado',
        verbose_name='Rol'
    )
    
    sucursal = models.ForeignKey(
        Sucursal, 
        on_delete=models.SET_NULL, 
        null=True, 
        verbose_name='Sucursal'
    )
    
    estado = models.CharField(
        max_length=20, 
        choices=ESTADO_CHOICES, 
        default='offline'
    )
    
    en_turno = models.BooleanField(
        default=False, 
        verbose_name='En turno activo'
    )
    
    foto = models.ImageField(
        upload_to='personal/', 
        blank=True, 
        null=True
    )
    
    telefono = models.CharField(
        max_length=20, 
        blank=True, 
        null=True
    )
    
    # Estandarización del campo de tiempo para evitar FieldErrors en Reportes/Vistas
    creado_en = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        verbose_name = 'Empleado'
        verbose_name_plural = 'Empleados'
        ordering = ['usuario__first_name']

    def nombre_completo(self):
        """Retorna el nombre del usuario o su username si no está definido."""
        return self.usuario.get_full_name() or self.usuario.username

    def foto_url(self):
        """Gestiona la URL de la foto o retorna un placeholder."""
        if self.foto and hasattr(self.foto, 'url'):
            return self.foto.url
        return 'https://placehold.co/40x40/f0eded/904800?text=' + self.nombre_completo()[0].upper()

    def badge_color(self):
        """Retorna las clases de Tailwind según el estado actual."""
        colores = {
            'activo':   'bg-green-50 text-green-700',
            'descanso': 'bg-orange-50 text-orange-700',
            'offline':  'bg-stone-100 text-stone-500',
        }
        return colores.get(self.estado, 'bg-stone-100 text-stone-500')

    def __str__(self):
        return f"{self.nombre_completo()} — {self.get_rol_display()}"


class Turno(models.Model):
    """
    Gestión de horarios por sucursal.
    """
    nombre = models.CharField(
        max_length=200, 
        verbose_name='Descripción'
    )
    
    sucursal = models.ForeignKey(
        Sucursal, 
        on_delete=models.SET_NULL, 
        null=True
    )
    
    personal = models.ManyToManyField(
        Empleado, 
        blank=True, 
        related_name='turnos'
    )
    
    # Estandarización de fecha para filtros consistentes
    fecha = models.DateField(
        verbose_name='Fecha'
    )
    
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    
    creado_en = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        verbose_name = 'Turno'
        verbose_name_plural = 'Turnos'
        ordering = ['fecha', 'hora_inicio']

    def __str__(self):
        return f"{self.nombre} — {self.fecha} ({self.sucursal})"


# Funciones auxiliares y nuevo modelo de Asistencia

def ruta_justificante(instance, filename):
    return f'justificantes/{instance.empleado.usuario.username}/{filename}'

class Asistencia(models.Model):
    ESTADO_CHOICES = [
        ('presente',  'Presente'),
        ('ausente',   'Ausente'),
        ('tardanza',  'Tardanza'),
        ('descanso',  'Día de Descanso'),
        ('vacaciones', 'Vacaciones'),
    ]

    empleado = models.ForeignKey(
        Empleado, 
        on_delete=models.CASCADE, 
        related_name='asistencias'
    )
    fecha = models.DateField(
        default=timezone.now, 
        verbose_name='Fecha'
    )
    hora_entrada = models.TimeField(
        null=True, 
        blank=True, 
        verbose_name='Hora de Entrada'
    )
    hora_salida = models.TimeField(
        null=True, 
        blank=True, 
        verbose_name='Hora de Salida'
    )
    estado = models.CharField(
        max_length=20, 
        choices=ESTADO_CHOICES, 
        default='ausente'
    )
    es_dia_descanso = models.BooleanField(
        default=False, 
        verbose_name='Día de Descanso'
    )
    justificante = models.FileField(
        upload_to=ruta_justificante, 
        blank=True, 
        null=True,
        verbose_name='Justificante de Ausencia'
    )
    notas = models.TextField(
        blank=True, 
        verbose_name='Notas'
    )
    # Nota: Asegúrate de que 'Sucursales.Usuario' sea la ruta correcta a tu modelo de usuario personalizado
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL,
        null=True, 
        blank=True, 
        related_name='asistencias_registradas'
    )

    class Meta:
        verbose_name = 'Asistencia'
        verbose_name_plural = 'Asistencias'
        ordering = ['-fecha', 'empleado__usuario__first_name']
        unique_together = ('empleado', 'fecha')

    @property
    def horas_trabajadas(self):
        if self.hora_entrada and self.hora_salida:
            from datetime import datetime, date
            entrada = datetime.combine(date.today(), self.hora_entrada)
            salida = datetime.combine(date.today(), self.hora_salida)
            diff = salida - entrada
            horas = diff.total_seconds() / 3600
            return round(horas, 2)
        return 0

    @property
    def tiene_justificante(self):
        return bool(self.justificante)

    def __str__(self):
        return f"{self.empleado} — {self.fecha} — {self.get_estado_display()}"
    

    