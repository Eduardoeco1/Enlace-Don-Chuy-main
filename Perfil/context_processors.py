# Perfil/context_processors.py
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from Inventario.models import Producto

def roles_y_notificaciones_globales(request):
    """
    Context processor unificado para Lama y Carbón.
    Proporciona los roles correctos mapeados uno a uno con base.html,
    la sucursal asignada dinámica/fija, el nombre del usuario y las alertas.
    """
    # ══════════════════════════════════════════════════════════════════
    # 1. ESTADO DE BASE (USUARIO NO AUTENTICADO)
    # ══════════════════════════════════════════════════════════════════
    if not request.user.is_authenticated:
        return {
            'es_empleado': False,
            'es_gerente': False,
            'es_duena': False,
            'notificaciones': [],
            'total_notificaciones': 0,
            'sucursal_actual': None,
            'sucursal_activa': None,
            'usuario_nombre': "Usuario"
        }
    
    user = request.user
    
    # ══════════════════════════════════════════════════════════════════
    # 2. EVALUACIÓN DE ROLES (CORREGIDO Y BLINDADO CONTRA ERRORES DE RELACIÓN)
    # ══════════════════════════════════════════════════════════════════
    rol_usuario = getattr(user, 'rol', '')
    if rol_usuario:
        rol_usuario = str(rol_usuario).strip().lower()

    # Base de permisos de superusuario o campo rol directo
    es_duena = user.is_superuser or rol_usuario in ['duena', 'dueña']
    es_gerente = (rol_usuario == 'gerente')
    
    perfil_empleado = None

    # Intento 1: Relación inversa normal (user.empleado)
    try:
        perfil_empleado = user.empleado
    except (AttributeError, Exception):
        # Intento 2: Búsqueda manual por si la relación inversa está corrupta u oculta
        try:
            from Personal.models import Empleado
            perfil_empleado = Empleado.objects.filter(usuario=user).first()
        except Exception:
            perfil_empleado = None

    # Si encontramos el perfil por cualquiera de los dos métodos, extraemos su rol
    if perfil_empleado:
        rol_empleado = getattr(perfil_empleado, 'rol', '')
        if rol_empleado and str(rol_empleado).strip().lower() == 'gerente':
            es_gerente = True

    # PARCHE DE RESCATE: Apoyo visual en desarrollo para gerentes sin relación explícita
    if not es_gerente and not es_duena:
        if 'gerente' in user.username.lower() or 'gerente' in user.first_name.lower():
            es_gerente = True
    
    # ══════════════════════════════════════════════════════════════════
    # 3. LÓGICA DEL SELECTOR GLOBAL DE SUCURSALES (CONTECTO DINÁMICO)
    # ══════════════════════════════════════════════════════════════════
    sucursal_actual = None

    if es_duena:
        # Dueña: usar sesión o None (todas las sucursales)
        sucursal_id = request.session.get('sucursal_global_id') or request.session.get('sucursal_activa_id')
        if sucursal_id:
            from Sucursales.models import Sucursal
            try:
                sucursal_actual = Sucursal.objects.get(id=int(sucursal_id))
            except (ValueError, Sucursal.DoesNotExist, Exception):
                sucursal_actual = None
    else:
        # Empleado/Gerente: extraer su sucursal fija predefinida
        sucursal_actual = getattr(user, 'sucursal', None)
        if not sucursal_actual and perfil_empleado:
            sucursal_actual = getattr(perfil_empleado, 'sucursal', None)
        
    # ══════════════════════════════════════════════════════════════════
    # 4. SISTEMA DE NOTIFICACIONES DINÁMICAS
    # ══════════════════════════════════════════════════════════════════
    notifs = []

    # A. Productos con stock crítico
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

    # B. Últimas entradas de mercancía (últimas 24h)
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

    # C. Justificantes pendientes de revisión (Solo para Gerente/Dueña)
    if es_gerente or es_duena:
        try:
            from Personal.models import Justificante
            pendientes = Justificante.objects.filter(estado='pendiente').count()
            if pendientes > 0:
                notifs.append({
                    'icono':   'rate_review',
                    'color':   'text-primary',
                    'titulo':  f'{pendientes} justificante(s) pendiente(s)',
                    'detalle': 'Requieren revisión',
                    'tipo':    'justificante',
                    'url':     reverse('Personal:control_justificantes'),
                })
        except Exception:
            pass

    # D. Asistencias pendientes (Solo para Gerente/Dueña)
    if es_gerente or es_duena:
        try:
            from Personal.models import Asistencia
            hoy = timezone.now().date()
            sin_entrada = Asistencia.objects.filter(
                fecha=hoy,
                hora_entrada=None,
                es_dia_descanso=False,
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

    # E. Mis justificantes rechazados (Para todos los empleados)
    if perfil_empleado:
        try:
            from Personal.models import Justificante
            hace_7_dias = timezone.now() - timedelta(days=7)
            rechazados = Justificante.objects.filter(
                empleado=perfil_empleado,
                estado='rechazado',
                fecha_revision__gte=hace_7_dias
            ).count()
            if rechazados > 0:
                notifs.append({
                    'icono':   'cancel',
                    'color':   'text-error',
                    'titulo':  f'{rechazados} justificante(s) rechazado(s)',
                    'detalle': 'Revisa los comentarios',
                    'tipo':    'rechazado',
                    'url':     reverse('Personal:mis_justificantes'),
                })
        except Exception:
            pass

    # ══════════════════════════════════════════════════════════════════
    # 5. CONSTRUCCIÓN DEL CONTEXTO FINAL PARA EL TEMPLATE
    # ══════════════════════════════════════════════════════════════════
    nombre_completo = f"{user.first_name} {user.last_name}".strip()
    
    return {
        # Mapeo de seguridad para base.html y barras laterales
        'es_empleado': not (es_gerente or es_duena),
        'es_gerente': es_gerente,
        'es_duena': es_duena,
        
        # Mapeo unificado de sucursal contextualizada
        'sucursal_actual': sucursal_actual,
        'sucursal_activa': sucursal_actual,  
        'usuario_nombre': nombre_completo or user.username,
        
        # Contenedores del sistema de alertas del navbar
        'notificaciones': notifs[:6],
        'total_notificaciones': len(notifs),
    }






