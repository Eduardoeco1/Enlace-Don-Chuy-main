from django.db import models
from django.contrib.auth.models import AbstractUser


class Sucursal(models.Model):
    nombre     = models.CharField(max_length=100)
    ubicacion  = models.CharField(max_length=255, blank=True)
    clave      = models.CharField(max_length=10, unique=True)
    activa     = models.BooleanField(default=True)
    creada_en  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Sucursal'
        verbose_name_plural = 'Sucursales'

    def __str__(self):
        return self.nombre


class Usuario(AbstractUser):
    ROL_CHOICES = [
        ('duena',    'Dueña'),
        ('gerente',  'Gerente'),
        ('empleado', 'Empleado'),
    ]

    rol      = models.CharField(max_length=20, choices=ROL_CHOICES, default='empleado')
    sucursal = models.ForeignKey(
        Sucursal,
        on_delete   = models.SET_NULL,
        null        = True,
        blank       = True,
        related_name= 'usuarios',
        verbose_name= 'Sucursal asignada',
    )

    # ── Helpers de rol ────────────────────────────
    @property
    def es_duena(self):
        return self.rol == 'duena' or self.is_superuser

    @property
    def es_gerente(self):
        return self.rol in ('gerente', 'duena') or self.is_superuser

    @property
    def es_empleado(self):
        return True  # todos tienen acceso mínimo

    def get_sucursal_activa(self, request):
        """
        Dueña puede cambiar contexto mediante sesión.
        Gerente/Empleado siempre ven su propia sucursal.
        """
        if self.es_duena:
            sid = request.session.get('sucursal_activa_id')
            if sid:
                try:
                    return Sucursal.objects.get(id=sid, activa=True)
                except Sucursal.DoesNotExist:
                    pass
            return None   # None = todas las sucursales
        return self.sucursal

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_rol_display()})"
    


    