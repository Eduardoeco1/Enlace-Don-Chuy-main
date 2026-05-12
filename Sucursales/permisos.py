from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.mixins import AccessMixin

# ══════════════════════════════════════════════
#  DECORADORES
# ══════════════════════════════════════════════

def rol_requerido(*roles_permitidos):
    """
    Verifica el rol del empleado en lugar del usuario base.
    """
    def decorador(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('/')
            
            # La Dueña (Superuser) siempre tiene acceso total
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            # Verificamos si el usuario tiene un perfil de Empleado y su rol
            try:
                perfil = request.user.empleado
                if perfil.rol in roles_permitidos:
                    return view_func(request, *args, **kwargs)
            except AttributeError:
                pass # El usuario no tiene perfil de empleado vinculado
            
            messages.error(request, '🚫 No tienes permiso para acceder a esta sección.')
            return redirect('/panel-control/')
        return _wrapped
    return decorador

def solo_duena(view_func):
    return rol_requerido('duena')(view_func)

def gerente_o_superior(view_func):
    # 'duena' es un rol que puedes asignar en Empleado, 
    # pero el decorador ya deja pasar a is_superuser
    return rol_requerido('gerente')(view_func)

def cualquier_rol(view_func):
    return rol_requerido('gerente', 'empleado')(view_func)

# ══════════════════════════════════════════════
#  HELPER: obtener sucursal del contexto actual
# ══════════════════════════════════════════════

def get_sucursal_contexto(request):
    """
    Lógica de filtrado de Enlace Don Chuy:
    1. Si es Superuser (Dueña): elige entre las 3 sucursales o ve todo.
    2. Si es Gerente/Empleado: forzamos sucursal asignada.
    """
    user = request.user
    if not user.is_authenticated:
        return None

    if user.is_superuser:
        # Aquí permitimos que la dueña filtre por sesión si seleccionó una sucursal
        sucursal_id = request.session.get('sucursal_seleccionada_id')
        if sucursal_id:
            from Sucursales.models import Sucursal
            return Sucursal.objects.filter(id=sucursal_id).first()
        return None # Ve todas las sucursales

    # Para Gerentes y Empleados, retornamos su sucursal fija
    try:
        return user.empleado.sucursal
    except AttributeError:
        return None
    
