from .models import Sucursal


def sucursal_contexto(request):
    """
    Disponible en todos los templates:
    - sucursal_activa: la sucursal filtrada actualmente
    - todas_sucursales: para el selector de la Dueña
    - es_duena, es_gerente: flags de rol
    """
    if not request.user.is_authenticated:
        return {}

    sucursal_activa = request.user.get_sucursal_activa(request)

    return {
        'sucursal_activa':  sucursal_activa,
        'todas_sucursales': Sucursal.objects.filter(activa=True) if request.user.es_duena else None,
        'es_duena':         request.user.es_duena,
        'es_gerente':       request.user.es_gerente,
        'rol_usuario':      request.user.get_rol_display() if hasattr(request.user, 'get_rol_display') else '',
    }


