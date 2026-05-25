import os
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify
from Sucursales.models import Sucursal  # Importación unificada del modelo Sucursal

class Empleado(models.Model):
    """
    Modelo principal para la gestión de personal en el sistema multisucursal.
    """
    ROLES_CHOICES = [
       
        ('gerente', 'Gerente'),
        ('empleado', 'Empleado'),
    ]

    ESTADO_CHOICES = [
        ('activo',   'Activo'),
        ('descanso', 'En Descanso'),
        ('offline',  'Offline'),
    ]

    DIAS_SEMANA = [
        (0, 'Lunes'),
        (1, 'Martes'),
        (2, 'Miércoles'),
        (3, 'Jueves'),
        (4, 'Viernes'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    ]

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='empleado'
    )
    
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
    
    dia_descanso_semanal = models.IntegerField(
        choices=DIAS_SEMANA,
        null=True,
        blank=True,
        verbose_name='Día de Descanso Semanal'
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
    
    creado_en = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        verbose_name = 'Empleado'
        verbose_name_plural = 'Empleados'
        ordering = ['usuario__first_name']

    def nombre_completo(self):
        return self.usuario.get_full_name() or self.usuario.username

    def foto_url(self):
        if self.foto and hasattr(self.foto, 'url'):
            return self.foto.url
        return 'https://placehold.co/40x40/f0eded/904800?text=' + self.nombre_completo()[0].upper()

    def badge_color(self):
        colores = {
            'activo':   'bg-green-50 text-green-700',
            'descanso': 'bg-orange-50 text-orange-700',
            'offline':  'bg-stone-100 text-stone-500',
        }
        return colores.get(self.estado, 'bg-stone-100 text-stone-500')

    def __str__(self):
        return f"{self.nombre_completo()} — {self.get_rol_display()}"


def ruta_justificante(instance, filename):
    username_limpio = slugify(instance.empleado.usuario.username)
    ext = filename.split('.')[-1]
    return f"justificantes/{username_limpio}_{instance.fecha}.{ext}"


class Asistencia(models.Model):
    """
    Sistema mejorado de asistencia con registro automático al login.
    """
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
    notas = models.TextField(
        blank=True, 
        verbose_name='Notas'
    )
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL,
        null=True, 
        blank=True, 
        related_name='asistencias_registradas'
    )
    registro_automatico = models.BooleanField(
        default=False,
        verbose_name='Registro Automático'
    )
    creado_en = models.DateTimeField(
        auto_now_add=True
    )
    actualizado_en = models.DateTimeField(
        auto_now=True
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

    def __str__(self):
        return f"{self.empleado} — {self.fecha} — {self.get_estado_display()}"


class Justificante(models.Model):
    """
    Modelo para la gestión de justificantes de ausencia del personal.
    """
    ESTADO_JUSTIFICANTE = [
        ('pendiente', 'Pendiente'),
        ('aprobado',  'Aprobado'),
        ('rechazado', 'Rechazado'),
    ]
    
    MOTIVO_CHOICES = [
        ('enfermedad', 'Enfermedad'),
        ('personal',   'Asunto Personal'),
        ('familiar',   'Asunto Familiar'),
        ('medico',     'Cita Médica'),
        ('otro',       'Otro'),
    ]

    empleado = models.ForeignKey(
        Empleado,
        on_delete=models.CASCADE,
        related_name='justificantes'
    )
    asistencia = models.ForeignKey(
        Asistencia,
        on_delete=models.CASCADE,
        related_name='justificantes',
        null=True,
        blank=True
    )
    fecha = models.DateField(
        verbose_name='Fecha de Ausencia'
    )
    motivo = models.CharField(
        max_length=20,
        choices=MOTIVO_CHOICES,
        default='otro',
        verbose_name='Motivo'
    )
    descripcion = models.TextField(
        verbose_name='Descripción'
    )
    archivo = models.FileField(
        upload_to=ruta_justificante,
        verbose_name='Archivo Adjunto',
        help_text='PDF, imagen o documento que respalde el justificante'
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_JUSTIFICANTE,
        default='pendiente',
        verbose_name='Estado'
    )
    revisado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='justificantes_revisados',
        verbose_name='Revisado Por'
    )
    comentario_revision = models.TextField(
        blank=True,
        verbose_name='Comentario de Revisión'
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True
    )
    fecha_revision = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Justificante'
        verbose_name_plural = 'Justificantes'
        ordering = ['-fecha_creacion']

    def aprobar(self, usuario, comentario=''):
        self.estado = 'aprobado'
        self.revisado_por = usuario
        self.comentario_revision = comentario
        self.fecha_revision = timezone.now()
        self.save()
        
        if self.asistencia:
            self.asistencia.estado = 'ausente'
            self.asistencia.notes = f"Justificado: {self.get_motivo_display()}"
            self.asistencia.save()

    def rechazar(self, usuario, comentario=''):
        self.estado = 'rechazado'
        self.revisado_por = usuario
        self.comentario_revision = comentario
        self.fecha_revision = timezone.now()
        self.save()

    def __str__(self):
        return f"{self.empleado} — {self.fecha} — {self.get_estado_display()}"


class Turno(models.Model):
    """
    PASO 1 (PROBLEMA 8): Modelo definitivo para gestionar turnos de empleados
    """
    TIPO_TURNO = [
        ('matutino', 'Matutino (8:00 - 13:00)'),
        ('vespertino', 'Vespertino (13:00 - 20:00)'),
        ('medio_tiempo', 'Medio Tiempo (Personalizado)'),
    ]
    empleado = models.ForeignKey(
        Empleado,
        on_delete=models.CASCADE,
        related_name='turnos_programados',
        null=True,
        blank=True
    )
    sucursal = models.ForeignKey(
        Sucursal,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Sucursal'
    )
    fecha = models.DateField(verbose_name='Fecha del Turno')
    tipo_turno = models.CharField(
        max_length=20,
        choices=TIPO_TURNO,
        default='matutino'
    )
    hora_inicio = models.TimeField(verbose_name='Hora de Inicio')
    hora_fin = models.TimeField(verbose_name='Hora de Fin')
    notas = models.TextField(blank=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='turnos_creados'
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Turno'
        verbose_name_plural = 'Turnos'
        ordering = ['fecha', 'hora_inicio']
        unique_together = ('empleado', 'fecha')
    
    def __str__(self):
        return f"{self.empleado} - {self.fecha} ({self.get_tipo_turno_display()})"
    
