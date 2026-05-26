from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def obtener_rol_usuario(user):
    """
    Obtiene el rol del usuario de forma segura.
    Revisa primero user.rol y luego user.empleado.rol.
    """
    if not user or not user.is_authenticated:
        return None

    if user.is_superuser:
        return 'duena'

    rol_user = getattr(user, 'rol', None)

    if rol_user:
        return rol_user

    try:
        empleado = user.empleado
        if empleado and empleado.rol:
            return empleado.rol
    except Exception:
        pass

    return None


def gerente_o_superior(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/')

        rol = obtener_rol_usuario(request.user)

        if request.user.is_superuser or rol in ['gerente', 'duena', 'dueña']:
            return view_func(request, *args, **kwargs)

        messages.error(request, '🚫 No tienes permiso para acceder a esta sección.')
        return redirect('/panel-control/')

    return _wrapped_view


def solo_duena(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/')

        rol = obtener_rol_usuario(request.user)

        if request.user.is_superuser or rol in ['duena', 'dueña']:
            return view_func(request, *args, **kwargs)

        messages.error(request, '🚫 Esta sección es exclusiva para la dueña.')
        return redirect('/panel-control/')

    return _wrapped_view


def cualquier_rol(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/')

        rol = obtener_rol_usuario(request.user)

        if request.user.is_superuser or rol in ['gerente', 'empleado', 'duena', 'dueña']:
            return view_func(request, *args, **kwargs)

        messages.error(request, '🚫 No tienes permiso para acceder a esta sección.')
        return redirect('/panel-control/')

    return _wrapped_view


def get_sucursal_contexto(request):
    if not request.user.is_authenticated:
        return None

    sucursal = getattr(request, 'sucursal_actual', None)

    if sucursal:
        return sucursal

    try:
        if request.user.empleado and request.user.empleado.sucursal:
            return request.user.empleado.sucursal
    except Exception:
        pass

    try:
        if request.user.sucursal:
            return request.user.sucursal
    except Exception:
        pass

    return None

