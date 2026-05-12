from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from Inventario.models import Producto

def notificaciones_globales(request):
    """
    Calcula notificaciones dinámicas con URLs de redirección para el navbar.
    """
    if not request.user.is_authenticated:
        return {'notificaciones': [], 'total_notificaciones': 0}

    notifs = []

    # 1. Productos con stock crítico
    try:
        criticos = Producto.objects.filter(activo=True)
        for p in criticos:
            if p.estado() in ('critico', 'agotado'):
                notifs.append({
                    'icono':   'warning',
                    'color':   'text-error',
                    'titulo':  f'Stock crítico: {p.nombre}',
                    'detalle': f'{p.stock} {p.unidad} restantes',
                    'tipo':    'critico',
                    'url':     reverse('Inventario:inventario'),
                })
    except Exception:
        pass

    # 2. Últimas entradas de mercancía (últimas 24h)
    try:
        from EntradaMercancia.models import EntradaInsumo
        hace_24h = timezone.now() - timedelta(hours=24)
        n_entradas = EntradaInsumo.objects.filter(creado_en__gte=hace_24h).count()
        if n_entradas > 0:
            notifs.append({
                'icono':   'inventory',
                'color':   'text-primary',
                'titulo':  f'{n_entradas} nueva(s) entrada(s) de mercancía',
                'detalle': 'Registradas en las últimas 24 horas',
                'tipo':    'info',
                'url':     reverse('EntradaMercancia:entrada'),
            })
    except Exception:
        pass

    # 3. Asistencias pendientes (Solo para Gerente/Dueña)
    try:
        # Asumiendo que 'es_gerente' es un atributo o propiedad de tu User custom
        if getattr(request.user, 'es_gerente', False) or getattr(request.user, 'es_duena', False):
            from Personal.models import Asistencia
            hoy = timezone.now().date()
            sin_entrada = Asistencia.objects.filter(
                fecha = hoy,
                hora_entrada = None,
                es_dia_descanso = False,
            ).count()
            
            if sin_entrada > 0:
                notifs.append({
                    'icono':   'badge',
                    'color':   'text-tertiary',
                    'titulo':  f'{sin_entrada} empleado(s) sin entrada',
                    'detalle': 'Revisa los registros de hoy',
                    'tipo':    'asistencia',
                    'url':     reverse('Personal:asistencias'),
                })
    except Exception:
        pass

    return {
        'notificaciones':       notifs[:6],  # Limitamos a las 6 más recientes
        'total_notificaciones': len(notifs),
    }




