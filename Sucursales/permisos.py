from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

# ══════════════════════════════════════════════
#  DECORADORES SIMPLIFICADOS E INFALIBLES
# ══════════════════════════════════════════════

def gerente_o_superior(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/')
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        try:
            perfil = request.user.empleado
            if perfil and perfil.rol in ['gerente', 'duena', 'dueña']:
                return view_func(request, *args, **kwargs)
        except Exception:
            pass
        messages.error(request, "🚫 No tienes permiso para acceder a esta sección.")
        return redirect('/panel-control/')
    return _wrapped_view

def solo_duena(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/')
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        try:
            if request.user.empleado.rol in ['duena', 'dueña']:
                return view_func(request, *args, **kwargs)
        except Exception:
            pass
        messages.error(request, "🚫 Esta sección es exclusiva para la dueña.")
        return redirect('/panel-control/')
    return _wrapped_view

def cualquier_rol(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/')
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        try:
            perfil = request.user.empleado
            if perfil and perfil.rol in ['gerente', 'empleado', 'duena', 'dueña']:
                return view_func(request, *args, **kwargs)
        except Exception:
            pass
        messages.error(request, "🚫 No tienes permiso para acceder a esta sección.")
        return redirect('/panel-control/')
    return _wrapped_view

# ══════════════════════════════════════════════
#  HELPER: OBTENER SUCURSAL DEL CONTEXTO ACTUAL
# ══════════════════════════════════════════════

def get_sucursal_contexto(request):
    """
    PUENTE DE COMPATIBILIDAD:
    Retorna la sucursal inyectada por el Middleware (request.sucursal_actual).
    Ya no hace lógica de base de datos ni validación de GET, 
    eliminando así el riesgo de errores de tipo (ValueError).
    """
    if not request.user.is_authenticated:
        return None
    
    # Simplemente devolvemos lo que el Middleware ya calculó y validó
    return getattr(request, 'sucursal_actual', None)





