from .models import Sucursal

def sucursal_contexto(request):
    if not request.user.is_authenticated:
        return {}

    user = request.user
    
    # 1. Recuperamos la sucursal del Middleware
    sucursal_activa = getattr(request, 'sucursal_actual', None)

    # 2. Lógica de roles (Tu lógica original intacta)
    es_duena = getattr(user, 'es_duena', False)
    es_gerente = getattr(user, 'es_gerente', False)
    rol_limpio = str(getattr(user, 'rol', '')).strip().lower()
    if rol_limpio == 'gerente': es_gerente = True
    elif rol_limpio in ['duena', 'dueña']: es_duena = True

    if not es_gerente and not es_duena:
        try:
            from Personal.models import Empleado
            emp = Empleado.objects.filter(usuario=user).first()
            if emp:
                rol_emp = str(getattr(emp, 'rol', '')).strip().lower()
                if rol_emp == 'gerente': es_gerente = True
                elif rol_emp in ['duena', 'dueña']: es_duena = True
        except Exception: pass

    rol_display = 'Empleado'
    if es_duena: rol_display = 'Dueña'
    elif es_gerente: rol_display = 'Gerente'

    # 3. Lógica de Sucursales (Simplificada para asegurar que llegue al HTML)
    todas_sucursales = Sucursal.objects.all()

    return {
        'sucursal_actual': sucursal_activa, # Nombre clave para el HTML
        'sucursales': todas_sucursales,      # Lista para el menú
        'es_duena': es_duena,
        'es_gerente': es_gerente,
        'es_empleado': not (es_gerente or es_duena),
        'rol_usuario': rol_display,
        'usuario_nombre': f"{user.first_name} {user.last_name}".strip() or user.username,
    }













