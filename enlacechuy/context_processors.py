from Sucursales.models import Sucursal

def sucursal_contexto(request):
    if not request.user.is_authenticated:
        return {}
        
    return {
        # Esta variable es la que leerán AMBOS botones
        'sucursal_actual': getattr(request, 'sucursal_actual', None),
        'sucursales': Sucursal.objects.all(),
    }


def negocio_context(request):
    return {
        "NOMBRE_NEGOCIO": "Enlace Don Chuy",
        "NOMBRE_NEGOCIO_MAYUS": "ENLACE DON CHUY",
        "NOMBRE_SISTEMA": "Sistema POS",
    }





