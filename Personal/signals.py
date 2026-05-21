"""
Señales para el módulo Personal.
Incluye registro automático de asistencia al login.
"""
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.utils import timezone
from .models import Asistencia


@receiver(user_logged_in)
def registrar_asistencia_automatica(sender, request, user, **kwargs):
    """
    Registra automáticamente la hora de entrada cuando el usuario inicia sesión.
    Solo si el usuario tiene un perfil de Empleado asociado.
    """
    try:
        empleado = user.empleado
        hoy = timezone.now().date()
        hora_actual = timezone.now().time()
        
        # Obtener o crear asistencia del día
        asistencia, created = Asistencia.objects.get_or_create(
            empleado=empleado,
            fecha=hoy,
            defaults={
                'hora_entrada': hora_actual,
                'estado': 'presente',
                'registro_automatico': True,
                'registrado_por': user
            }
        )
        
        # Si ya existe pero no tiene hora de entrada, la registramos
        if not created and not asistencia.hora_entrada:
            asistencia.hora_entrada = hora_actual
            asistencia.estado = 'presente'
            asistencia.registro_automatico = True
            asistencia.registrado_por = user
            asistencia.save()
            
        # Verificar si es el día de descanso del empleado
        dia_semana_actual = hoy.weekday()  # 0=Lunes, 6=Domingo
        
        # Si la asistencia tiene definido un día de descanso y coincide con hoy
        if asistencia.dia_descanso_semanal is not None:
            if dia_semana_actual == asistencia.dia_descanso_semanal:
                asistencia.es_dia_descanso = True
                asistencia.estado = 'descanso'
                asistencia.save()
                
    except AttributeError:
        # El usuario no tiene perfil de empleado, no hacer nada
        pass
    except Exception as e:
        # Registrar cualquier otro error pero no bloquear el login
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error al registrar asistencia automática: {e}")
        